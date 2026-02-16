from datetime import datetime
from app.extensions import db

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
