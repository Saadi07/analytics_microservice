from pymongo import MongoClient

MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
MONGO_DB_NAME = "test"
        
def connect_mongo():
    try:
        client = MongoClient(MONGO_URL)
        db = client[MONGO_DB_NAME]
        return db
    except Exception as e:
        raise RuntimeError(f"Error connecting to MongoDB: {e}")