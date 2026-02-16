"""
Development environment configuration
"""
from config.default import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
