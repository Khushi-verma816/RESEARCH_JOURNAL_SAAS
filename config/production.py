"""
Production environment configuration
"""
from config.default import Config

class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
