"""
Tenant model for multi-tenancy
"""
from datetime import datetime
from app.extensions import db

class Tenant(db.Model):
    """Tenant/Organization model for multi-tenancy"""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subdomain = db.Column(db.String(100), unique=True, nullable=False, index=True)
    custom_domain = db.Column(db.String(255), nullable=True, unique=True)
    
    # Contact Information
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Address
    address_line1 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Settings
    logo_url = db.Column(db.String(500), nullable=True)
    theme_color = db.Column(db.String(7), default='#007bff')
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Limits (based on subscription)
    max_users = db.Column(db.Integer, default=5)
    max_storage_gb = db.Column(db.Integer, default=10)
    max_journals = db.Column(db.Integer, default=3)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    journals = db.relationship('Journal', backref='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'email': self.email,
            'is_active': self.is_active
        }