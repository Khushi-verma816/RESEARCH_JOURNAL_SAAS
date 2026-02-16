from datetime import datetime
from app.extensions import db

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    price_monthly = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    status = db.Column(db.String(20), default='trial')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
