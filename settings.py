import os

try:
    from password import USERNAME, PASSWORD
except:
    raise ValueError("Specify username/password in `password.py` "
                     "under the same folder!")

try:
    # Specify your nginx folder or somewhere
    from password import XML_DIR
except:
    XML_DIR = os.path.dirname(os.path.abspath(__file__))

# Mongodb settings
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.caixin

# 404 sign
sign_of_404 = '<title>404_'
