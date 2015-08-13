"""

Skeleton yet.

"""
import logging

log = logging.getLogger(__name__)

from models import db_connect, create_engine, insert_item, create_tables
from sqlalchemy.orm import sessionmaker
from utils import load_session_or_login
from workflow import Workflow, next_states, final_state


class SpiderWorkflow(Workflow):
    '''
    Full workflow that performs incremental crawling
    '''

    def __init__(self):
        super(SpiderWorkflow, self).__init__()
        self._error = ''

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

        # Get database session for add and commit sql_item
        db_engine = db_connect()
        create_tables(db_engine)
        _session = sessionmaker(bind=db_engine)
        self.db_session = _session()

        # Run actual spider code non-blockingly
        self.goto('update_issues')

    @next_states('parse_all_issues')
    def update_issues(self):
        """
        Fetch remote available issues and record locally.

        :return:
        """
        self.goto('parse_all_issues')

    @next_states('update_articles')
    def parse_all_issues(self):
        """
        test
        """
        # if any article in any issue has not been downloaded yet
        # will pass [articles to fetch] to next state

        self.goto('update_articles')

    @next_states('generate_ebook')
    def update_articles(self):
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
