"""
Database models
"""
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

# Association tables for many-to-many relationships
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    
    # Basic Info
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref='users')
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

class Role(db.Model):
    """Role model for RBAC"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Tenant(db.Model):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subdomain = db.Column(db.String(100), unique=True, nullable=False)
    
    # Subscription
    subscription_plan = db.Column(db.String(50), default='free')
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tenant {self.name}>'

class Journal(db.Model):
    """Journal/Publication model"""
    __tablename__ = 'journals'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Basic Info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_accepting_submissions = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='journal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Journal {self.name}>'

class Submission(db.Model):
    """Manuscript submission model"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    
    # Files
    manuscript_file_url = db.Column(db.String(500), nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='submitted')
    
    # Dates
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='submissions')
    reviews = db.relationship('Review', backref='submission', lazy='dynamic')
    
    def __repr__(self):
        return f'<Submission {self.title}>'

class Review(db.Model):
    """Peer review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review content
    comments = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    
    # Recommendation
    recommendation = db.Column(db.String(50), nullable=True)
    
    # Status
    status = db.Column(db.String(50), default='pending')
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reviewer = db.relationship('User', backref='reviews')
    
    def __repr__(self):
        return f'<Review {self.id}>'

class BlogPost(db.Model):
    """Blog post model"""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(255), nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    
    # Status
    is_published = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    author = db.relationship('User', backref='blog_posts')
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'

class AIConversation(db.Model):
    """AI conversation model"""
    __tablename__ = 'ai_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(255), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('AIMessage', backref='conversation', lazy='dynamic')
    
    def __repr__(self):
        return f'<AIConversation {self.id}>'

class AIMessage(db.Model):
    """AI message model"""
    __tablename__ = 'ai_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('ai_conversations.id'), nullable=False)
    
    # Content
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIMessage {self.id}>'