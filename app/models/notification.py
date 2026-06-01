from datetime import datetime

from app.core.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), default='general', nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Notification {self.id} user={self.user_id} read={self.is_read}>'
