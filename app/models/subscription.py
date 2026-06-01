# app/models/subscription.py

from app.core.extensions import db
from datetime import datetime, timedelta

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id              = db.Column(db.Integer, primary_key=True)
    tenant_id       = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Plan: free / pro / enterprise
    plan            = db.Column(db.String(50), default='free')

    # Status: active / cancelled / expired / trialing
    status          = db.Column(db.String(50), default='active')

    # Billing
    amount          = db.Column(db.Float, default=0.0)
    currency        = db.Column(db.String(10), default='INR')
    billing_cycle   = db.Column(db.String(20), default='monthly')

    # Dates
    started_at      = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at      = db.Column(db.DateTime, nullable=True)
    cancelled_at    = db.Column(db.DateTime, nullable=True)
    trial_ends_at   = db.Column(db.DateTime, nullable=True)

    # Payment reference (for future Stripe integration)
    stripe_customer_id      = db.Column(db.String(200), nullable=True)
    stripe_subscription_id  = db.Column(db.String(200), nullable=True)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    tenant          = db.relationship('Tenant', backref='subscription', uselist=False)

    # ── Plan Limits ──────────────────────────────
    PLAN_LIMITS = {
        'free': {
            'articles':     10,
            'members':       3,
            'journals':      1,
            'ai_requests':   5,
            'custom_domain': False,
            'analytics':     False,
            'video':         False,
            'price':         0,
        },
        'pro': {
            'articles':     -1,   # unlimited
            'members':      -1,
            'journals':     -1,
            'ai_requests':  100,
            'custom_domain': True,
            'analytics':     True,
            'video':         True,
            'price':         49,
        },
        'enterprise': {
            'articles':     -1,
            'members':      -1,
            'journals':     -1,
            'ai_requests':  -1,
            'custom_domain': True,
            'analytics':     True,
            'video':         True,
            'price':         0,   # Custom
        },
    }

    @property
    def limits(self):
        return self.PLAN_LIMITS.get(self.plan, self.PLAN_LIMITS['free'])

    @property
    def is_active(self):
        if self.status == 'cancelled':
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    @property
    def is_trial(self):
        if self.trial_ends_at:
            return datetime.utcnow() < self.trial_ends_at
        return False

    @property
    def days_remaining(self):
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return max(0, delta.days)
        return None

    def can_add_article(self, current_count):
        limit = self.limits['articles']
        if limit == -1:
            return True
        return current_count < limit

    def can_add_member(self, current_count):
        limit = self.limits['members']
        if limit == -1:
            return True
        return current_count < limit

    def __repr__(self):
        return f'<Subscription {self.plan} [{self.status}]>'
