try:
    from password import USERNAME, PASSWORD
except:
    raise ValueError("Specify username/password at `password.py` "
                     "under the same folder!")

# Mongodb settings
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.caixin

# 404 sign
sign_of_404 = '<title>404_'
