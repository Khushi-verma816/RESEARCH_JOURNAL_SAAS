from .default import Config


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"

    
    SQLALCHEMY_DATABASE_URI = "sqlite:///research_dev.db"
