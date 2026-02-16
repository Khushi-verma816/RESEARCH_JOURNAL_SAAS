from flask import Flask
from flask_login import LoginManager
from app.extensions import db
from app.models.user import User


def create_app():
    app = Flask(__name__)

    # App Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    # Journal blueprint
    try:
        from app.routes.journal import journal_bp
        app.register_blueprint(journal_bp, url_prefix='/journal')
    except ImportError:
        print("Journal blueprint not found.")

    # Create database tables
    with app.app_context():
        db.create_all()

    # DEBUG: Print routes
    print("\n" + "="*50)
    print("REGISTERED ROUTES:")
    print("="*50)
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{methods:10s} {rule.rule}")
    print("="*50 + "\n")

    return app
