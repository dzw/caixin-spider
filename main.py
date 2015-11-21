import asyncio
import datetime
import logging
import os
import PyRSS2Gen
from models import Article
from settings import db
from utils import CaixinRegex
from utils import load_session_or_login, get_body
from settings import XML_DIR

log = logging.getLogger(__name__)
logging.basicConfig(level='INFO')


class Spider:
    '''
    Full workflow that performs incremental crawling
    '''

    def __init__(self):

        # Issue links: ('http://magazine.caixin.com/2012/cw533/', ...)
        self.old_issues = set()
        self.new_issues = set()

        # By default it won't go back to 1998
        self.fetch_old_articles = True

        # {date: [link], ...}
        self.articles = dict()

        # final articles to crawl: [link, ...]
        self.articles_to_fetch = set()

        # Latest issue link to generate rss
        self.latest_issue_date = None

        # Event loop, aiohttp Session
        self.loop = asyncio.get_event_loop()
        self.session = load_session_or_login()

    def init(self):
        """
        Check if network and database are working.
        """
        # Create index for MongoDB
        db.articles.create_index('date')
        db.articles.create_index('link')
        db.articles.create_index('title')

        db.issues.create_index('date')
        db.issues.create_index('articles')

        db.not_found_articles.create_index('link')

    def update_issues(self):
        """
        Fetch issue links of 2010.1 - now, generate links from 1998.4 - 2009.11
        """
        weekly_home_page = self.loop.run_until_complete(get_body(self.session, "http://weekly.caixin.com/"))
        weekly_home_page = weekly_home_page.decode('utf-8')

        # Part 1: 2010 - now
        new_issues = CaixinRegex.issue_2010_2015.findall(weekly_home_page)[0]
        new_issue_links = CaixinRegex.issue_2010_2015_link.findall(new_issues)

        # The latest issue is not there, so manually add it
        last_issue = new_issue_links[0]
        last_issue_id = CaixinRegex.issue_id.findall(last_issue)[0]
        latest_issue_id = int(CaixinRegex.issue_id.findall(last_issue)[0]) + 1
        latest_issue_link = last_issue.replace(last_issue_id,  str(latest_issue_id))
        self.new_issues = set(new_issue_links)
        self.new_issues.add(latest_issue_link)

        # Also add its date for later RSS generation
        cover = CaixinRegex.cover.findall(weekly_home_page)[0]
        latest_issue_date = CaixinRegex.old_issue_date.findall(cover)[0]
        self.latest_issue_date = latest_issue_date

        # Part 2: 1998.4 - 2009.11
        # Format: http://magazine.caixin.com/h/1998-04.html
        if self.fetch_old_articles:
            old_issue_format = 'http://magazine.caixin.com/h/{}-{}.html'
            start_date = datetime.date(1998, 4, 1)
            end_date = datetime.date(2009, 11, 2)
            while start_date < end_date:
                year, month = start_date.year, str(start_date.month).zfill(2)
                self.old_issues.add(old_issue_format.format(year, month))
                start_date += datetime.timedelta(days=30)

    @asyncio.coroutine
    def parse_single_issue(self, *, issue_link, old=False):
        """
        Parse single issue link, append links to self.articles
        """
        page_response = yield from self.session.get(issue_link)
        page = yield from page_response.read_and_close()
        page = page.decode('utf-8')

        if not old:
            try:
                page = CaixinRegex.new_issue_main_content.findall(page)[0]
            except:
                # issue in 2010 has no such a main content thing
                pass

        # separate article by date: {'2006-06-26': [article link1, ...]}
        articles_in_this_month = CaixinRegex.old_issue_link.findall(page)
        article_dates = set(CaixinRegex.old_issue_date.findall(page))
        monthly_articles = {date: [link for link in articles_in_this_month if date in link] for date in article_dates}

        # Delete date with no articles
        valid_monthly_articles = {date: monthly_articles[date] for date in monthly_articles if monthly_articles[date]}

        # Append links into self.articles
        for date in valid_monthly_articles:
            articles = valid_monthly_articles[date]
            log.debug('Date {}: {} articles.'.format(date, len(articles)))
            if date in self.articles:
                self.articles[date] += articles
            else:
                self.articles[date] = articles

    def parse_issues(self):
        """
        Feed all articles into dict self.articles
        """
        f1 = asyncio.wait([self.parse_single_issue(issue_link=old_issue_link, old=True)
                           for old_issue_link in self.old_issues])

        f2 = asyncio.wait([self.parse_single_issue(issue_link=new_issue_link)
                           for new_issue_link in self.new_issues])

        if self.fetch_old_articles:
            self.loop.run_until_complete(f1)
        self.loop.run_until_complete(f2)

    def generate_downloading_items(self):
        # check article link if in database then, check if downloaded, if so skip
        # no need to check article length, for example:
        # http://weekly.caixin.com/2015-07-03/100824881.html has length of only 128..

        # Result in self.articles_to_fetch, a list

        for date in self.articles:
            articles = self.articles[date]
            for link in articles:
                article_exist = db.articles.find_one({'link': link})
                if not article_exist:
                    self.articles_to_fetch.add(link)

                elif article_exist['length'] == 0:
                    log.error('Article {} has length of 0'.format(link))

                # confirmed 404 articles should be removed
                confirmed_404 = db.not_found_articles.find_one({'link': link})
                if confirmed_404 and confirmed_404['confirmed']:
                    self.articles_to_fetch.remove(link)

        log.info('{} new articles to fetch.'.format(len(self.articles_to_fetch)))

    def update_articles(self):
        # Download all articles_to_fetch

        # asyncio.wait will warp coroutines into Tasks, which would be
        # executed non-blockingly
        try:
            self.loop.run_until_complete(asyncio.wait(
                [Article(link=link, session=self.session).save() for link in self.articles_to_fetch])
            )
        except ValueError:
            # ValueError: Set of coroutines/Futures is empty.
            log.info('No new articles yet.')

    def generate_feed(self):
        xml_path = os.path.join(XML_DIR, 'caixin_rss.xml')

        # Find latest articles and convert into rss format
        articles_of_this_issue = list(db.articles.find({'date': self.latest_issue_date}))
        for article in articles_of_this_issue:
            article['description'] = article['content_html']
            article['pubDate'] = datetime.datetime.strptime(article['date'], '%Y-%m-%d')
            del article['date']
            del article['content']
            del article['content_html']
            del article['_id']
            del article['length']

        rss_items = [PyRSS2Gen.RSSItem(**item) for item in articles_of_this_issue]

        rss = PyRSS2Gen.RSS2(
            title="Caixin Weekly {}".format(self.latest_issue_date),
            link="Somewhere",
            description="Caixin Weekly full text",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items,
        )

        with open(xml_path, "wb") as rss_path:
            rss.write_xml(rss_path)

    def run(self):
        self.init()
        self.update_issues()
        self.parse_issues()
        self.generate_downloading_items()
        self.update_articles()
        self.generate_feed()
        log.info('Done. {} issues, {} articles, {} 404 articles in total!'.format(
            db.issues.count(), db.articles.count(), db.not_found_articles.count()
        ))
        self.session.close()

if __name__ == '__main__':
    spider = Spider()
    spider.run()
