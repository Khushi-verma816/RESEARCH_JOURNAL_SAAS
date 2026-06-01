# app/models/user.py

from app.core.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)

    # Which tenant this user belongs to (NULL = super admin)
    tenant_id    = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)

    # Basic Info
    first_name   = db.Column(db.String(100), nullable=False)
    last_name    = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(200), unique=True, nullable=False)
    password_hash= db.Column(db.String(512), nullable=False)

    # Role
    # super_admin  → controls entire platform
    # tenant_owner → owns a journal organization
    # editor       → can approve/reject articles
    # author       → can submit articles
    # reviewer     → can review articles
    # subscriber   → read only
    role         = db.Column(db.String(50), default='subscriber')

    # Status
    is_verified  = db.Column(db.Boolean, default=False)
    is_active    = db.Column(db.Boolean, default=True)

    # Profile
    avatar_url   = db.Column(db.String(500), nullable=True)
    bio          = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)

    # Password Reset
    reset_token  = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    notifications = db.relationship(
        'Notification',
        backref='recipient',
        lazy='dynamic',
        foreign_keys='Notification.user_id',
        cascade='all, delete-orphan',
    )

    # ── Password ─────────────────────────────────
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate a password reset token valid for 1 hour"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None

    # ── Properties ───────────────────────────────
    @property
    def full_name(self):
        first = (self.first_name or '').strip()
        last = (self.last_name or '').strip()
        return f'{first} {last}'.strip() or self.email

    @property
    def initials(self):
        first = (self.first_name or '').strip()
        last = (self.last_name or '').strip()
        if first and last:
            return f'{first[0]}{last[0]}'.upper()
        if first:
            return first[0].upper()
        if last:
            return last[0].upper()
        return 'U'

    # ── Role Checks ──────────────────────────────
    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_admin(self):
        return self.role in ['admin', 'super_admin']

    def is_tenant_owner(self):
        return self.role in ['tenant_owner', 'super_admin']

    def is_editor(self):
        return self.role in ['editor', 'tenant_owner', 'admin', 'super_admin']

    def is_author(self):
        return self.role in ['author', 'editor', 'tenant_owner', 'admin', 'super_admin']

    def is_reviewer(self):
        return self.role in ['reviewer', 'editor', 'tenant_owner', 'admin', 'super_admin']

    def can_manage_tenant(self):
        return self.role in ['tenant_owner', 'admin', 'super_admin']

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
