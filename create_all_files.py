"""
Auto-generate all project files
"""
import os
 
def create_file(path, content):
    """Create a file with content"""
    dir_path = os.path.dirname(path)
    if dir_path:  # Only create directory if path has a directory
        os.makedirs(dir_path, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

# Configuration files
files = {
    'config/__init__.py': '''"""
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
''',

    'config/default.py': '''"""
Default configuration settings
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
    DEBUG = False
    TESTING = False
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'Research Journal SaaS')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///research_journal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@yourapp.com')
    
    # Security
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    BCRYPT_LOG_ROUNDS = 12
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
''',

    'config/development.py': '''"""
Development environment configuration
"""
from config.default import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
''',

    'config/production.py': '''"""
Production environment configuration
"""
from config.default import Config

class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
''',

    'app/extensions.py': '''"""
Flask extensions initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
bcrypt = Bcrypt()

# Login manager configuration
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    from app.models.user import User
    return User.query.get(int(user_id))
''',

    'app/__init__.py': '''"""
Application factory
"""
from flask import Flask
from config import get_config
from app.extensions import db, migrate, login_manager, mail, bcrypt

def create_app(config_name=None):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        app.config.from_object(get_config())
    else:
        from config import config_by_name
        app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Simple home route
    @app.route('/')
    def index():
        return '<h1>Research Journal SaaS</h1><p>Application is running!</p>'
    
    return app
''',

    'app/models/__init__.py': '''"""
Database models package
"""
''',

    'app/models/user.py': '''"""
User model
"""
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, bcrypt

class User(UserMixin, db.Model):
    """User model"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.check_password_hash(self.password_hash, password)
''',

    'app/routes/__init__.py': '''"""
Routes package initialization
"""
''',

    'app/routes/auth.py': '''"""
Authentication routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return '<h2>Login Page</h2><p>Login form will go here</p>'

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return '<h2>Register Page</h2><p>Registration form will go here</p>'

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
''',

    'wsgi.py': '''"""
WSGI entry point for production
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
''',

    'seed_db.py': '''"""
Seed database with initial data
"""
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    
    print("Checking for existing users...")
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Created admin user: admin@example.com / admin123")
    else:
        print("ℹ️ Admin user already exists")
    
    print("✅ Database seeded successfully!")
'''
}

# Create all files
print("Creating all project files...\n")
for filepath, content in files.items():
    create_file(filepath, content)

print("\n" + "="*50)
print("✅ ALL FILES CREATED SUCCESSFULLY!")
print("="*50)
print("\nNext steps:")
print("1. Run: flask db init")
print("2. Run: flask db migrate -m 'Initial migration'")
print("3. Run: flask db upgrade")
print("4. Run: python seed_db.py")
print("5. Run: flask run")