"""
Application factory
"""
from flask import Flask, render_template

def create_app(config_name=None):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        from config import get_config
        app.config.from_object(get_config())
    else:
        from config import config_by_name
        app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    from app.extensions import db, login_manager
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # Optional extensions (try to load, skip if not available)
    try:
        from app.extensions import migrate
        migrate.init_app(app, db)
    except:
        pass
    
    try:
        from app.extensions import mail
        mail.init_app(app)
    except:
        pass
    
    try:
        from app.extensions import bcrypt
        bcrypt.init_app(app)
    except:
        pass
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.journal import journal_bp
    from app.routes.admin import admin_bp
    from app.routes.blog import blog_bp
    from app.routes.ai import ai_bp
    from app.routes.upload import upload_bp
    from app.routes.profile import profile_bp
    from app.routes.search import search_bp
    from app.routes.analytics import analytics_bp
    
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(journal_bp, url_prefix='/journal')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(search_bp, url_prefix='/search')  
    app.register_blueprint(analytics_bp, url_prefix='/analytics')  

    # Home route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return '<h1>404 - Page Not Found</h1>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return '<h1>500 - Internal Server Error</h1>', 500
    
    return app