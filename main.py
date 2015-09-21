"""

Skeleton yet.

"""
import datetime
import logging
import re
from models import db_connect, create_engine, insert_item, create_tables
from utils import CaixinRegex
from sqlalchemy.orm import sessionmaker
from utils import load_session_or_login
from workflow import Workflow, next_states, final_state

log = logging.getLogger(__name__)


class SpiderWorkflow(Workflow):
    '''
    Full workflow that performs incremental crawling
    '''

    def __init__(self):
        super(SpiderWorkflow, self).__init__()
        self._error = ''

        self.old_issues = set()
        self.new_issues = set()
        self.articles = dict()

        # TODO: issues and articles runner

    @next_states('update_issues', initial=True)
    def init(self):
        """
        Check if network and database are working.
        """
        # Get requests.session
        try:
            self.session = load_session_or_login()
        except ArithmeticError:
            self._error = 'Network error!'
            self.goto('error')

        # TODO:
        # Either: Get existing database(check tables and columns)
        # Or: Create new database according to models.py
        # db_engine = db_connect()
        # create_tables(db_engine)
        # _session = sessionmaker(bind=db_engine)
        # self.db_session = _session()

        # Run actual spider code non-blockingly
        self.goto('update_issues')

    @next_states('parse_all_issues')
    def update_issues(self):
        """
        Fetch remote available issues and record locally.

        :return:
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

        self.goto('parse_old_issues')

    def parse_old_issue(self, issue_link):
        """
        Parse single old issue like, return links
        :return dict monthly_articles: {'2006-06-26': [article link1, ...]}
        """
        # TODO: Make this non-blockingly
        page = self.session.get(issue_link)

        # separate article by date
        articles_in_this_month = CaixinRegex.old_issue_link.findall(page.text)
        article_dates = set(CaixinRegex.old_issue_date.findall(page.text))
        monthly_articles = {date: [link for link in articles_in_this_month if date in link] for date in article_dates}
        return monthly_articles

    @next_states('parse_new_issues')
    def parse_old_issues(self):
        """
        Check if any old issue has no articles inside(by month?!)
        """
        # TODO: Make this non-blockingly
        for old_issue_link in list(self.old_issues)[:2]:
            articles_in_that_month = self.parse_old_issue(old_issue_link)
            self.articles.update(articles_in_that_month)

        self.goto('parse_new_issues')

    @next_states('update_articles')
    def parse_new_issues(self):
        """
        test
        """
        # if any article in any issue has not been downloaded yet
        # will pass [articles to fetch] to next state

        # Loop over every issue's link
        # TODO: asynchronously do this
        # TODO: maybe add a runner when __init__
        # TODO: move this function to somewhere else, make the workflow clean
        # 1. update existing issues with info: publish date, title(the cover article), ...
        # 2. access url of each issue: a navigation to their article links
        # 3. check article link if in database then, check if downloaded, if so skip
        # 4. else append new row to Articles Table, goto next stage
        self.goto('update_articles')

    @next_states('generate_ebook')
    def update_articles(self):
        # TODO: asynchoronously do this too, might contain lots of articles
        # for each article.. 
        # 
        self.goto('generate_ebook')

    @next_states('done')
    def generate_ebook(self):
        # Generate ebooks and push to subscribers' kindle

        # TODO:
        # Maintain subscribers and their state
        # Incrementally send ebook of each issue to their inbox

        self.goto('done')

    @final_state
    def done(self):
        print(self.seen_states)
        print('done')
        pass

    @final_state
    def error(self):
        log.error(self._error)


if __name__ == '__main__':
    spider = SpiderWorkflow()
    spider.run()
