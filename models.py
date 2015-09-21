"""

ORM is used for convenience.

Database usage:
 - db_connect: validate settings
 - create_table: in case first time open
 - get session: see insert_item(),
    ref -> http://docs.sqlalchemy.org/en/rel_1_0/orm/session.html
 - use this session to add and commit new sql_item

"""

from sqlalchemy import create_engine, Column, String, \
    Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import relationship, backref
import re
import settings

from sqlalchemy.ext.declarative import declarative_base
DeclarativeBase = declarative_base()


def db_connect():
    """
    Validate database settings and
    :return: a METHOD to create session, usage(after get return):
      session = Session()

    """
    # TODO: need to check/increase available pool size?
    engine = create_engine(URL(**settings.DATABASE))

    try:
        engine.connect()
        engine.dispose()
    except (OperationalError, ):
        raise ValueError("Check database settings!")

    return engine

def create_tables(engine):
    """
    Initialize database, WON'T break existing data.
    This actions take some time(about 0.015~0.02s), so make it happen once,
    only when start crawling.
    """
    DeclarativeBase.metadata.create_all(engine)

def insert_item(session, sql_item):
    """
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    :param session:
    :param sql_item: Issue or Article
    :return:
    """
    try:
        session.add(sql_item)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class Issue(DeclarativeBase):

    __tablename__ = 'issue'

    # Example: http://weekly.caixin.com/2015/cw658/index.html
    # 豪门与“山寨”之盟 <- Cover story
    # 2015年6月29日出版 <- publish_date
    # 总期号：660 <- id

    id = Column(Integer, primary_key=True)
    publish_date = Column(DateTime)
    cover_story = Column(String)
    url = Column(String)

    # TODO: make sure this works for both direction, get articles under issue
    # and get issue from article.

    # - issue = someIssue()
    # - issue.articles.all()

    # - article = someArticle()
    # - article.relate_issue.articles.all()

    # ref: http://stackoverflow.com/questions/7420670/how-do-i-access-the-related-foreignkey-object-from-a-object-in-sqlalchemy
    # ref: http://docs.sqlalchemy.org/en/rel_1_0/orm/relationships.html
    articles = relationship('Article', backref='issue')

    def next_issue(self):
        pass

    def previous_issue(self):
        pass


class Article(DeclarativeBase):

    __tablename__ = 'article'

    # Example:
    # http://weekly.caixin.com/[2015-01-02]/[100770279].html

    # id = 20150102100770279, date + id
    id = Column(Integer, primary_key=True)
    url = Column(String)

    abstract = Column(String, nullable=True)
    author = Column(String, nullable=True)

    # Origin article content is in json: {'content': content, ...}
    # http://tag.caixin.com/news/NewsV51.jsp?id=100828060&page=0&rand=0.945020263781771
    # where:
    #  - `id` is article id(looks unique, but still add 8-digit date for safe..)
    #  - `page=0` to get full text
    #  - `rand' is random.random(), totally optional.. guess it's just for fun?
    title = Column(String, nullable=True)
    content = Column(String, nullable=True)
    content_plain_html = Column(String, nullable=True)

    # TODO: convenient 1-to-many query for both
    # articles under same issue and publish date
    relate_issue = Column(Integer, ForeignKey('issue.id'))

    # After scraping mark this article as downloaded
    downloaded = Column(Boolean, default=0)

    def update_content(self, session):
        """

        :param session: a logged_in requests session
        :return:
        """
        # article_url = 'http://weekly.caixin.com/2015-07-10/100828041.html'
        article_url = self.url
        article_content = session.get(article_url)
        java = session.get('http://tag.caixin.com/news/NewsV51.jsp?id=100828060&page=0&rand=0.4237610185518861')
        article_content_re = re.compile('(?<=resetContentInfo\()[\s\S]*(?=\);)')

        # content
        article = eval(article_content_re.findall(article_content.text)[0])['content']

        # Clean html to text, leave only <p> tag
        from lxml.html.clean import Cleaner
        cleaner = Cleaner(allow_tags=['p'], remove_unknown_tags=False)
        cleaned_text = cleaner.clean_html(article)
        cleaned_text = cleaned_text.replace('\u3000', ' ') # content_plain_html



def test():

    engine = db_connect()
    create_tables(engine)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    aaa = Issue(id=1, publish_date='20150101')
    session.add(aaa)
    session.commit()
    # import ipdb; ipdb.set_trace()
    bbb = Article(id='2', url='123', content='123', relate_issue=1)
    session.add(bbb)
    session.commit()
    session.query(Article)


def destroy_database():
    #TODO:
    pass
