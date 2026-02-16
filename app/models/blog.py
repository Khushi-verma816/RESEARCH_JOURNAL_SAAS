"""
Blog models
"""
from datetime import datetime
from app.extensions import db

class BlogPost(db.Model):
    """Blog post model"""
    
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, published
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Engagement
    views_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='blog_posts')
    tenant = db.relationship('Tenant', backref='blog_posts')
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'