"""

Skeleton yet.

"""
import asyncio
import datetime
import logging
from models import Article
from settings import db
from utils import CaixinRegex
from utils import load_session_or_login

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

        # {date: [link], ...}
        self.articles = dict()

        # final articles to crawl: [link, ...]
        self.articles_to_fetch = set()

    def init(self):
        """
        Check if network and database are working.
        """
        # Get requests.session
        self.session = load_session_or_login()

        # Create index for mongo
        db.articles.create_index('date')
        db.articles.create_index('link')
        db.articles.create_index('title')

        db.issues.create_index('date')
        db.issues.create_index('articles')

    def update_issues(self):
        """
        Fetch issue links of 2010.1 - now, generate links from 1998.4 - 2009.11
        """
        weekly_home_page = self.session.get("http://weekly.caixin.com/")

        # Part 1: 2010 - now
        new_issues = CaixinRegex.issue_2010_2015.findall(weekly_home_page.text)[0]
        new_issue_links = CaixinRegex.issue_2010_2015_link.findall(new_issues)
        self.new_issues = set(new_issue_links)

        # Part 2: 1998.4 - 2009.11
        # Format: http://magazine.caixin.com/h/1998-04.html
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
        page_response = self.session.get(issue_link)

        if page_response.status_code == 200:
            page = page_response.text
        else:
            raise ValueError("link {} did'n t give correct response")

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
            log.info('Date {}: {} articles.'.format(date, len(articles)))
            if date in self.articles:
                self.articles[date] += articles
            else:
                self.articles[date] = articles

    def parse_issues(self):
        """
        Feed all articles into dict self.articles
        """
        f1 = asyncio.wait([self.parse_single_issue(issue_link=old_issue_link, old=True)
                           for old_issue_link in list(self.old_issues)[:1]])

        f2 = asyncio.wait([self.parse_single_issue(issue_link=new_issue_link)
                           for new_issue_link in list(self.new_issues)[:1]])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(f1)
        loop.run_until_complete(f2)

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

        log.info('{} new articles to fetch.'.format(len(self.articles_to_fetch)))

    def update_articles(self):
        # Download all articles_to_fetch

        # asyncio.wait will warp coroutines into Tasks, which would be
        # executed non-blockingly
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(
            [Article(link=link, session=self.session).save() for link in self.articles_to_fetch])
        )
        loop.close()

    def generate_ebook(self):
        # Generate ebooks and push to subscribers' kindle

        # TODO:
        # Maintain subscribers and their state
        # Incrementally send ebook of each issue to their inbox
        pass

    def run(self):
        self.init()
        self.update_issues()
        self.parse_issues()
        self.generate_downloading_items()
        self.update_articles()
        self.generate_ebook()

if __name__ == '__main__':
    spider = Spider()
    spider.run()
