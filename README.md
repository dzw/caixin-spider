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

If you want to clean html, install `lxml` package by yourself, confirm using `from lxml.html.clean import Cleaner`.

## Run

After installed MongoDB, run these commands:

    python3 -m venv ../.env/"${PWD##*/}"  # virtualenv -p /usr/bin/python3 ../.env/caixin-spider
    source ../.env/"${PWD##*/}"/bin/activate
    pip install -r requirements.txt
    python main.py

If you want articles from 1998 to 2009, change `self.fetch_old_articles` to `True` in `main.py`.

RSS feed location is by default the same folder as `main.py`, specify custom location in `settings.py` to overwrite it:

    XML_DIR = '/usr/share/nginx'

## Run on Debian 7

Debian 7 currently have default python version of 3.2, the project used some grammer that requires higher version, thus `pyenv` is recommended:

    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    source ~/.bashrc

    pyenv install 3.4.3
    pyenv virtualenv 3.4.3 ../.env/"${PWD##*/}"
    pyenv shell "${PWD##*/}"

    pip install -r requirements.txt
    python main.py

Remain commands are the same as above.

## TODO

* Improve speed
