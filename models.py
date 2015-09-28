try:
    from lxml.html.clean import Cleaner
    cleaner = Cleaner(allow_tags=['p'], remove_unknown_tags=False)
except ImportError:
    def cleaner(something):
        return something

from settings import db, sign_of_404
from utils import CaixinRegex
import logging
import random
import asyncio

log = logging.getLogger(__name__)


class Article:

    def __init__(self, *, link, session):
        # link: http://magazine.caixin.com/2013-10-11/100590480.html
        # date: yyyy-mm-dd
        # content: requests.get(link).text, smartly decoded text
        self.link = link
        self.date = CaixinRegex.old_issue_date.findall(link)[0]
        self.content = None
        self.id = self.date.replace('-', '') + CaixinRegex.article_id.findall(self.link)[0]
        self.session = session

    @asyncio.coroutine
    def download(self):
        # Construct download link
        article_id = CaixinRegex.article_id.findall(self.link)[0]
        content_link = CaixinRegex.content_link.format(article_id, random.random())

        # subtract json from javascript response
        # which contains: current page, media count, total page count
        contents = self.session.get(content_link)

        # Deal with 404
        if sign_of_404 in contents.text:
            return ''

        # If any content
        try:
            contents_json = eval(CaixinRegex.article_content.findall(contents.text)[0])
        except:
            log.error(contents.text)
            contents_json = {'totalPage': 1, 'content': ''}

        # If page is split into more than 1, it should be revealed in the json
        # However, sometimes it is 0 ...
        if contents_json['totalPage'] > 1 or \
                (contents_json['totalPage'] != 1 and not contents_json['content']):
            content_link = content_link.replace('page=1', 'page=0')
            contents = self.session.get(content_link)
            contents_json = eval(CaixinRegex.article_content.findall(contents.text)[0])

        log.debug('Article {} has been downloaded'.format(self.link))
        # assert len(contents_json['content']) > 0

        return contents_json['content']

    @asyncio.coroutine
    def get_title(self):
        page = self.session.get(self.link)
        title = CaixinRegex.article_title.findall(page.text)
        if not title:
            log.debug('>>> article {} has no title'.format(self.link))
            title = ['Untitled']
        return title[0]

    @asyncio.coroutine
    def to_json(self):
        self.content = yield from self.download()
        title = yield from self.get_title()

        # With only html tag <p> (and unknown tags) left
        # 404 blank string would raise lxml.etree.ParserError, too lazy to import
        try:
            cleaned_text = cleaner.clean_html(self.content)
            cleaned_text = cleaned_text.replace('\u3000', ' ')
        except:
            cleaned_text = self.content

        article_json = {
            '_id': self.id,
            'link': self.link,
            'date': self.date,
            'content': cleaned_text,
            'content_html': self.content,
            'length': len(self.content),
            'title': title,
        }
        return article_json

    @asyncio.coroutine
    def save(self):
        # Save to 2 tables: article, issue
        if db.articles.find({'link': self.link}).count() == 0:
            article_json = yield from self.to_json()

            # if 404 twice, article would be save to db.not_found_articles
            if article_json['length'] < 5:
                log.debug('Article {} seems to be 404, check if true.'.format(self.link))
                if db.not_found_articles.find({'link': self.link}).count() == 0:
                    db.not_found_articles.insert_one({'link': self.link, 'confirmed': 0})
                else:
                    db.not_found_articles.update({'link': self.link}, {'$set': {
                        'confirmed': 1}
                    })
                return True

            db.articles.insert_one(article_json)
            log.info('Article {} of date {} saved to database'.format(
                self.link, self.date))

            # Issues table will be updated with appended article links
            # each issue: {'id': ..., 'date': ..., 'articles': [...]}
            if db.issues.find({'date': self.date}).count() == 0:
                log.debug('Issue {} created'.format(self.date))
                db.issues.insert_one({'date': self.date, 'articles': [self.link]})
            else:
                current_issue = db.issues.find_one({'date': self.date})
                articles_on_current_issue = current_issue['articles']
                old_articles_count = len(articles_on_current_issue)
                articles_on_current_issue.append(self.link)
                db.issues.update({'date': self.date}, {'$set': {
                    'articles': articles_on_current_issue}
                })
                log.debug('updated issue {}, from {} articles to {}'.format(
                    self.date, old_articles_count, old_articles_count + 1))

        # If already founded in database
        else:
            log.debug('Article {} is already in database'.format(self.link))

        return True


def destroy_database():
    db.articles.drop()
    db.issues.drop()
