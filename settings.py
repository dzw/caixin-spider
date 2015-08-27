# SQL settings

import os
from password import USERNAME as username, PASSWORD as password

USERNAME = username
PASSWORD = password

# for docker-machine user, there will be a environtment variable
if 'DOCKER_HOST' in os.environ:
    import re
    ip_filter = re.compile('(?<=\/\/).*(?=:)')
    ip = ip_filter.findall(os.environ['DOCKER_HOST'])
    assert len(ip) == 1 # 
else:
    raise ValueError('Fill your database info')

DATABASE = {
    'drivername': 'postgres',
    'host': ip[0],
    'port': 15432,
    'username': 'dbuser',
    'password': 'dbpass',
    'database': 'caixin',
}

