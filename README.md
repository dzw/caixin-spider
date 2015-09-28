# Crawler for Caixin Weekly

Incrementally/non-blockingly crawl articles from 1998.4 till now, using python3 and mongodb, then generate RSS feed for later use.

## Prerequisites

**Python3**

Packages:

    pip install -r requirements.txt

**Database**: install MongoDB and change `settings.py` if necessary.

**Username\&password**: check Hackpad for the credentials or buy your own ones, fill into `password.py` in format:

    USERNAME = 'some_username'
    PASSWORD = 'some_password'

## Run

After installed MongoDB, run these commands:

    python3 -m venv ../.env/"${PWD##*/}"
    source ../.env/"${PWD##*/}"/bin/activate
    pip install -r requirements.txt
    python main.py

If you want articles from 1998 to 2009, change `self.fetch_old_articles` to `True` in `main.py`.

RSS feed location is by default the same folder as `main.py`, specify custom location in `settings.py` to overwrite it:

    XML_DIR = '/usr/share/nginx'

## TODO

* alternatives for `lxml` package? (bit troublesome to install in new Ubuntu)

* Improve speed
