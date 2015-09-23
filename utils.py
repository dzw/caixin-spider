"""

Utils including:
 - login
 - issue browsing/article processing regex
 - database check and create

"""
import logging
import os
import pickle
import re
import requests
import settings

log = logging.getLogger(__name__)

# Save pickle session to the same folder as login.py
session_name = 'caixin.p'
abs_path = os.path.realpath(__file__)
session_path = abs_path.replace(__file__, session_name)


class CaixinRegex:

    # Some regex that are used when scraping

    # Issue link:
    # - start in 'weekly' or 'magazine' followed up with `caixin`, 2010 - now
    # those are founded in `http://weekly.caixin.com/`, in different format:
    # http://weekly.caixin.com/2015/cw660/index.html <- CaiXinZhouKan
    # http://magazine.caixin.com/2014/cw610/index.html <- XinShiJi
    # without `index.html` it also works.
    issue_2010_2015 = re.compile('wangqi[\s\S]*?gdqk')
    issue_2010_2015_link = re.compile('http.*cw\d+\/')
    issue_id = re.compile('(?<=cw)\d+')

    # Article link:
    # - new
    new_issue_main_content = re.compile('(?<=class="mainMagContent">)[\s\S]*?(?=bottom)')

    # - old
    # Cover article need a "view full article conversion"
    # sample: http://magazine.caing.com/2010/cwcs422/
    old_issue_link = re.compile('http.*?\d\d\d\d\d\d+\.html')
    old_issue_date = re.compile('\d\d\d\d-\d\d-\d\d')

    # Content:
    article_id = re.compile('\d\d\d\d\d+')
    article_title = re.compile('(?<=<h1>)[\s\S]*?(?=</h1>)')
    content_link = 'http://tag.caixin.com/news/NewsV51.jsp?id={}&page=1&rand={}'
    article_content = re.compile('(?<=resetContentInfo\()[\s\S]*(?=\);)')


def load_session_or_login():
    """

    :return: a requests.session() that available for crawling
    """
    try:
        session = pickle.load(open(session_path, 'rb'))

        # Get user's home page to verify:
        # - should contain cookies
        # - didn't timeout, get a new page to check
        try:
            logged_in = session.get('http://user.caixin.com/', timeout=3)
            log.debug("session loaded with username {}".format(dict(session.cookies)['SA_USER_USER_NAME']))
            if 'Welcome' not in logged_in.text:
                raise ValueError
        except:
            # network is slow, check connection
            raise ArithmeticError

        return session

    except (TypeError, FileNotFoundError, ValueError):
        # TypeError: didn't use open(filename, 'rb')
        # FileNotFoundError: file not found
        # ValueError: didn't use python3, unsupported pickle protocol;
        #  or just lost login session.
        log.debug('No pickle found, will log in now...')
        return login()


def login():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/43.0.2357.81 Safari/537.36',
        'Referer': 'http://user.caixin.com/usermanage/login/',
        'Via': 'Copyright@2014 Caixin'
    }
    data = dict(
        username=settings.USERNAME,
        password=settings.PASSWORD,
        cookietime=31536000  # seems TTL of cookies
    )

    # Init cookies
    session = requests.session()
    session.headers.update(headers)
    session.get('http://weekly.caixin.com/')

    # Go to login page
    login_url = 'http://user.caixin.com/usermanage/login/'
    session.get(login_url)

    # Login
    # this POST would automatically set cookies for session
    k = session.post(login_url, data=data)
    logged_in = session.get('http://user.caixin.com/')
    if 'SA_USER_auth' in k.headers['set-cookie']:
        log.info('user {} login succeed!'.format(data['username']))
        _logged = True
    else:
        raise OverflowError("BOMB! Didn't log in!")

    # Dump to the same folder as login.py
    pickle.dump(session, open(session_path, 'wb'))

    return session

if __name__ == '__main__':
    load_session_or_login()
