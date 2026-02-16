"""
Subscription and payment models
"""
from datetime import datetime, timedelta
from app.extensions import db

class SubscriptionPlan(db.Model):
    """Subscription plan model"""
    
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Pricing
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    price_yearly = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Limits
    max_users = db.Column(db.Integer, default=5)
    max_storage_gb = db.Column(db.Integer, default=10)
    max_journals = db.Column(db.Integer, default=3)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price_monthly': float(self.price_monthly),
            'max_users': self.max_users
        }

class Subscription(db.Model):
    """Subscription model"""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='trial')  # trial, active, canceled
    
    # Dates
    trial_end = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='subscription')
    plan = db.relationship('SubscriptionPlan')
    
    def __repr__(self):
        return f'<Subscription {self.id}>'
    
    def start_trial(self, days=14):
        """Start trial period"""
        self.status = 'trial'
        self.trial_end = datetime.utcnow() + timedelta(days=days)