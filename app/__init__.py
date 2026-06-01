from flask import Flask
from config import config
from app.core.extensions import db, migrate, login_manager, mail, csrf
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, 'connect')
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA journal_mode=MEMORY')
    cursor.execute('PRAGMA synchronous=OFF')
    cursor.close()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    with app.app_context():
        from app.models.custom_domain import CustomDomainRequest
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.article import Article
        from app.models.notification import Notification
        from app.models.subscription import Subscription
        from app.models.transaction import Transaction
        from app.models.testimonial import Testimonial

        from app.core.middleware import detect_tenant
        app.before_request(detect_tenant)

        from app.modules.auth import auth_bp
        from app.modules.auth import routes as auth_routes
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from app.modules.admin import admin_bp
        from app.modules.admin import routes as admin_routes
        app.register_blueprint(admin_bp, url_prefix='/admin')

        from app.modules.tenants import tenants_bp
        from app.modules.tenants import routes as tenant_routes
        app.register_blueprint(tenants_bp, url_prefix='/tenants')

        from app.modules.articles import articles_bp
        from app.modules.articles import routes as article_routes
        app.register_blueprint(articles_bp, url_prefix='/articles')

        from app.modules.billing import billing_bp
        from app.modules.billing import routes as billing_routes
        app.register_blueprint(billing_bp, url_prefix='/billing')

        from app.modules.profile import profile_bp
        from app.modules.profile import routes as profile_routes
        app.register_blueprint(profile_bp)

        from app.modules.search import search_bp
        from app.modules.search import routes as search_routes
        app.register_blueprint(search_bp)

        from app.modules.analytics import analytics_bp
        from app.modules.analytics import routes as analytics_routes
        app.register_blueprint(analytics_bp)

        from app.modules.team import team_bp
        from app.modules.team import routes as team_routes
        app.register_blueprint(team_bp)

        from app.modules.video import video_bp
        from app.modules.video import routes as video_routes
        app.register_blueprint(video_bp)

        from app.modules.ai import ai_bp
        from app.modules.ai import routes as ai_routes
        app.register_blueprint(ai_bp, url_prefix="/ai")

        from app.modules.main import main_bp
        from app.modules.main import routes as main_routes
        app.register_blueprint(main_bp)

        from app.core.errors import register_error_handlers
        register_error_handlers(app)

    return app