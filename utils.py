"""

Utils including:
 - login
 - issue browsing/article processing regex
 - database check and create

"""
from models import db_connect
import os
import pickle
import requests
import settings

# Save pickle session to the same folder as login.py
session_name = 'caixin.p'
abs_path = os.path.realpath(__file__)
session_path = abs_path.replace(__file__, session_name)

def load_session_or_login():
    """

    :return: a requests.session() that available for crawling
    """
    try:
        session = pickle.load(open(session_path, 'rb'))

        # Get user's home page to verify:
        # - should contain cookies
        # - didn't timeout, get a new page to check
        logged_in = session.get('http://user.caixin.com/')
        if 'base_info' not in logged_in.text:
            raise ValueError

        return session
    except (TypeError, FileNotFoundError, ValueError):
        # TypeError: didn't use open(filename, 'rb')
        # FileNotFoundError: file not found
        # ValueError: didn't use python3, unsupported pickle protocol;
        #  or just lost login session.
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
    if 'SA_USER_auth' in k.headers['set-cookie'] \
            and 'base_info' in logged_in.text:
        # log.info('login succeed!')
        _logged = True
    else:
        raise OverflowError("BOMB! Didn't log in!")

    # Dump to the same folder as login.py
    pickle.dump(session, open(session_path, 'wb'))

    return session

if __name__ == '__main__':
    load_session_or_login()
