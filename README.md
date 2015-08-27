## Prerequisites

**Python3**

**Dependencies**:

    pip install -r requirements.txt
    
Notice here, postgres driver `psycopg2` requires a `pg_config`, which requires installing postgresql first:

    brew install postgresql # on OS X
    sudo apt-get install libpq-dev # on Debian/Ubuntu

**Username\&password**: check Hackpad for the credentials, fill into `password.py`, settings.py would import it.
 
**Database**: default settings are compatible with the following docker commands.

    docker pull sameersbn/postgresql:9.4-3
    docker run --name caixinpsql -e 'DB_USER=dbuser' -e 'DB_PASS=dbpass' -e 'DB_NAME=caixin' -p 15432:5432 -d sameersbn/postgresql:9.4-3

Where `caixinpsql` is docker container's name, 3 `-e` to specify database settings, `docker_ip:15432` is where we access the database.

You can change if you'd like to.

## Run(NOT Implemented):

Ideally:

    source ~/dev/env/python3/bin/activate
    python main.py

## Database Management

Directly login from your docker host:

    psql -h 192.168.50.128 -p 15432 -d caixin -U dbuser

And input `dbpass`.

Notice that by default postgres does not allow peer authentication from localhost.

## TODO

* Actual spider code(WAT?) with incremental updating check(only fetch latest issue that not recorded locally)

* Non-blocking mechanism

* Ebook generation and push system

* Apply Workflow system to incremental updating: check Issue(if new parse new else check article), check articles(unfinished ones), generate to-crawl-list(if blank done), send to non-blocking engine. (just an idea, ref [repo](https://github.com/rbarrois/xworkflows))

* Fix (hopefully) all FIXME(s) and TODO(s)

* Organize README.md
