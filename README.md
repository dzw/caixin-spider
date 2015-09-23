# Crawler for Caixin Weekly

Incrementally/non-blockingly crawl articles from 1998.4 till now, using python3 and mongodb.

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

## TODO

* alternatives for `lxml` package? (bit troublesome to install in new Ubuntu)

* Validate local contents for `to-fetch-links`

* Improve speed

* Ebook generation and push system

* Fix (hopefully) all FIXME(s) and TODO(s)
