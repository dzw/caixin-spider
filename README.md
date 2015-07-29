## Development Status&Tip

ONLY login snippets and database backend has been implemented.

Tips:

- try setup travis/dockerhub script, sqlite3 would be good(i guess).
- dev on branch(looks more friendly, but not sure how to do code review..)

## Prerequisites

Python3: avoid encoding issue.

Dependencies:

    pip install -r requirements.txt
    
Username\&password: check Hackpad for the credentials, fill into `settings.py`.
 
Database: setup database environment, then fill into `settings.py`.

## Run(NOT Implemented):

Ideally:

    source ~/dev/env/python3/bin/activate
    python main.py


## TODO

* FIND A CODER!!

* Actual spider code(WAT?) with incremental updating check(only fetch latest issue that not recorded locally)

* Non-blocking mechanism

* Ebook generation and push system

* Introduce Workflow system for incremental updating: check Issue(if new parse new else check article), check articles(unfinished ones), generate to-crawl-list(if blank done), send to non-blocking engine. (just an idea, ref [repo](https://github.com/rbarrois/xworkflows)) 
