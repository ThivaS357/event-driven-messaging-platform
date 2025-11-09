import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from datetime import datetime


mongo_client = None
mongo_db = None

def get_db_connection(ConfigClass):
    
    global mongo_client, mongo_db
    
    try:
        uri = ConfigClass.MONGO_URI
        db_name = ConfigClass.MONGO_DATABASE_NAME
    except AttributeError:
        print("ERROR: Provided configuration object is missing MONGO_URI or MONGO_DATABASE_NAME.")
        return None, None
    
    if mongo_client !=None and mongo_db!=None:
        return mongo_client, mongo_db
    
    try:
        client = MongoClient(uri)
        client.server_info()

        db = client[db_name]
        
        mongo_client = client
        mongo_db = db
        
        return client, db
    
    except ConnectionFailure as error:
        print(f"ERROR: Failed to connect to MongoDB: {error}")
        return None, None
    except ConfigurationError as error:
        print(f"ERROR: Invalid MongoDB URI: {error}")
        return None, None
    except Exception as error:
        print(f"ERROR: An unexpected error occurred: {error}")
        return None, None
    
def utc_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")