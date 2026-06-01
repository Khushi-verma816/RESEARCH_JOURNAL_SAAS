# app/models/custom_domain.py

from app.core.extensions import db
from datetime import datetime

class CustomDomainRequest(db.Model):
    __tablename__ = 'custom_domain_requests'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Domain details
    custom_domain = db.Column(db.String(200), nullable=False)
    domain_type = db.Column(db.String(50), default='Domain')  # Domain, Subdomain
    origin_url = db.Column(db.String(500), nullable=True)  # Original subdomain URL

    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected

    # Dates
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_date = db.Column(db.DateTime, nullable=True)

    # Approval details
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Additional info
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = db.relationship('Tenant', backref='custom_domain_requests')
    approved_by = db.relationship('User', backref='approved_domains', foreign_keys='CustomDomainRequest.approved_by_id')

    @property
    def school_name(self):
        """Return the tenant/school name"""
        return self.tenant.name if self.tenant else 'Unknown'

    @property
    def admin_users(self):
        """Return all admin users for this tenant"""
        if not self.tenant:
            return []
        from app.models.user import User
        return User.query.filter(
            User.tenant_id == self.tenant_id,
            User.role.in_(['admin', 'super_admin', 'tenant_owner'])
        ).all()

    @property
    def primary_admin(self):
        """Return the first admin user for this tenant"""
        admins = self.admin_users
        return admins[0] if admins else None

    @property
    def admin_display_name(self):
        """Return formatted admin name for display"""
        admin = self.primary_admin
        if admin:
            return f"{admin.full_name} ({admin.role.replace('_', ' ').title()})"
        return 'No Admin'

    @property
    def full_origin_url(self):
        """Return the full origin URL"""
        if self.origin_url:
            return self.origin_url
        if self.tenant:
            return f"https://edusynergy.in/{self.tenant.subdomain}"
        return ''

    def approve(self, admin_user_id):
        """Approve the custom domain request"""
        self.status = 'approved'
        self.approved_date = datetime.utcnow()
        self.approved_by_id = admin_user_id

        # Also update the tenant's custom domain
        if self.tenant:
            self.tenant.custom_domain = self.custom_domain

        db.session.commit()

    def reject(self):
        """Reject the custom domain request"""
        self.status = 'rejected'
        db.session.commit()

    def __repr__(self):
        return f'<CustomDomainRequest {self.custom_domain} [{self.status}]>'
