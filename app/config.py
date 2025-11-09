import os


class Config:
    
    MONGO_URI = os.getenv('MONGO_URI') or "mongodb://127.0.0.1:27017/event_driven_message_platform?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.9"
    
    MONGO_DATABASE_NAME = "event_driven_message_platform"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False