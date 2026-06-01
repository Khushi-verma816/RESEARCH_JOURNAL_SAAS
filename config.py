import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _is_usable_sqlite_uri(uri):
    if not uri.startswith('sqlite:///'):
        return True
    db_name = uri.replace('sqlite:///', '', 1).strip()
    if not db_name or db_name == ':memory:':
        return True
    base_dir = Path(__file__).resolve().parent
    db_path = Path(db_name)
    if not db_path.is_absolute():
        db_path = base_dir / 'instance' / db_path
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute('SELECT name FROM sqlite_master LIMIT 1').fetchone()
        return True
    except sqlite3.Error:
        return False

def _resolve_database_uri():
    default_uri = 'sqlite:///researchforge.db'
    configured_uri = os.environ.get('DATABASE_URL') or default_uri
    if configured_uri.startswith('sqlite:///') and not _is_usable_sqlite_uri(configured_uri):
        return default_uri
    return configured_uri

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = 'Research Hub'
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_CURRENCY = os.environ.get('RAZORPAY_CURRENCY', 'INR')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'noreply@researchhub.com')

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = False

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
