# app/models/transaction.py

from app.core.extensions import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id              = db.Column(db.Integer, primary_key=True)
    tenant_id       = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=True)

    amount          = db.Column(db.Float, nullable=False, default=0.0)
    currency        = db.Column(db.String(10), default='INR')
    status          = db.Column(db.String(50), default='pending')
    payment_method  = db.Column(db.String(50), default='online')
    plan            = db.Column(db.String(50), nullable=True)
    reference_id    = db.Column(db.String(200), nullable=True)
    notes           = db.Column(db.Text, nullable=True)

    approved_by_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at     = db.Column(db.DateTime, nullable=True)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant       = db.relationship('Tenant', backref='transactions')
    approved_by  = db.relationship('User', foreign_keys=[approved_by_id])

    @property
    def status_label(self):
        return {
            'pending':   ('⏳', 'amber'),
            'completed': ('✓',  'green'),
            'failed':    ('✕',  'red'),
            'refunded':  ('↩',  'sky'),
        }.get(self.status, ('?', 'muted'))

    def __repr__(self):
        return f'<Transaction INR {self.amount} [{self.status}]>'
