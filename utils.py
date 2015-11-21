"""

Utils including:
 - login
 - issue browsing/article processing regex
 - database check and create

"""
import aiohttp
import asyncio
import logging
import os
import pickle
import re
import settings

log = logging.getLogger(__name__)

# Save pickle session to the same folder as login.py
session_name = 'caixin.p'
abs_path = os.path.realpath(__file__)
session_path = abs_path.replace(__file__, session_name)


headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/43.0.2357.81 Safari/537.36',
        'Referer': 'http://user.caixin.com/usermanage/login/',
        'Via': 'Copyright@2014 Caixin'
    }


async def get_body(client, url):
    async with client.get(url) as response:
        return await response.read()

async def post_data(client, url, data):
    async with client.post(url=url, data=data) as response:
        return await response.read()


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
    # - cover article of latest issue
    cover = re.compile('(?<=tit>)[\s\S]*?(?=\/dt)')

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

    :return: a aiohttp.ClientSession() that available for crawling
    """
    try:
        conn = aiohttp.TCPConnector(limit=settings.conn_limit)
        loop = asyncio.get_event_loop()
        with open(session_path, 'rb') as cookies:
            session_cookies = pickle.load(cookies)
        session = aiohttp.ClientSession(loop=loop, headers=headers,
                                        connector=conn, cookies=session_cookies)

        # Get user's home page to verify:
        # - should contain cookies
        # - didn't timeout, get a new page to check
        try:
            logged_in = loop.run_until_complete(get_body(session, 'http://user.caixin.com/'))
            log.debug("session loaded with username {}".format(dict(session.cookies)['SA_USER_USER_NAME']))
            if 'Welcome' not in logged_in.decode('utf-8'):
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
    data = dict(
        username=settings.USERNAME,
        password=settings.PASSWORD,
        cookietime=31536000  # seems TTL of cookies
    )

    # Init with headers and connection limit
    conn = aiohttp.TCPConnector(limit=settings.conn_limit)
    loop = asyncio.get_event_loop()
    session = aiohttp.ClientSession(loop=loop, headers=headers, connector=conn)

    _ = loop.run_until_complete(get_body(session, 'http://weekly.caixin.com/'))

    # Go to login page
    login_url = 'http://user.caixin.com/usermanage/login/'
    _ = loop.run_until_complete(get_body(session, login_url))

    # Login
    # this POST, if succeed, would automatically set cookies for session
    login_json = loop.run_until_complete(post_data(session, login_url, data))

    logged_in = False
    try:
        login_result_1 = eval(login_json.decode('utf-8'))
        if login_result_1['code'] == 1:
            logged_in = True
    except KeyError:
        if 'SA_USER_auth' in session.cookies:
            logged_in = True

    if not logged_in:
        raise ValueError("Didn't log in successfully, check your codes.")

    # aiohttp.Session itself is not serializable, dump its
    # cookies and load back later
    pickle.dump(session.cookies, open(session_path, 'wb'))

    return session

if __name__ == '__main__':
    load_session_or_login()
