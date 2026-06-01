# app/models/tenant.py

from app.core.extensions import db
from datetime import datetime

class Tenant(db.Model):
    __tablename__ = 'tenants'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150), nullable=False)
    subdomain      = db.Column(db.String(100), unique=True, nullable=False)
    custom_domain  = db.Column(db.String(200), unique=True, nullable=True)
    description    = db.Column(db.Text, nullable=True)

    # Status
    is_active      = db.Column(db.Boolean, default=True)
    is_verified    = db.Column(db.Boolean, default=False)

    # Subscription
    plan           = db.Column(db.String(50), default='free')  # free, pro, enterprise

    # White Label Branding
    logo_url       = db.Column(db.String(500), nullable=True)
    favicon_url    = db.Column(db.String(500), nullable=True)
    primary_color  = db.Column(db.String(10),  default='#0272c6')
    secondary_color= db.Column(db.String(10),  default='#38adf8')
    footer_text    = db.Column(db.String(300),  nullable=True)
    custom_css     = db.Column(db.Text,         nullable=True)

    # Contact
    contact_email  = db.Column(db.String(200),  nullable=True)
    website_url    = db.Column(db.String(300),  nullable=True)

    # Owner (who created this tenant)
    owner_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Timestamps
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users          = db.relationship('User', backref='tenant',
                                     lazy='dynamic',
                                     foreign_keys='User.tenant_id')

    # ── Helpers ──────────────────────────────────
    @property
    def full_url(self):
        if self.custom_domain:
            return f'https://{self.custom_domain}'
        return f'http://{self.subdomain}.localhost:5000'

    @property
    def member_count(self):
        return self.users.count()

    def __repr__(self):
        return f'<Tenant {self.name} ({self.subdomain})>'