import os 
from .default import Config 

class ProductionConfig(Config) :
    DEBUG = False
    ENV = "production"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True