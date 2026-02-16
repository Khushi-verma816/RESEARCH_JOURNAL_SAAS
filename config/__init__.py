"""
Configuration module
"""
import os
from config.default import Config
from config.development import DevelopmentConfig
from config.production import ProductionConfig

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': Config
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, Config)
