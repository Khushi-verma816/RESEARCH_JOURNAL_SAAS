# app/models/article.py

from app.core.extensions import db
from datetime import datetime

class Article(db.Model):
    __tablename__ = 'articles'

    id              = db.Column(db.Integer, primary_key=True)

    # Which journal this belongs to
    tenant_id       = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Who submitted it
    author_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Who is reviewing it
    reviewer_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Who approved/rejected it
    editor_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Content
    title           = db.Column(db.String(500),  nullable=False)
    abstract        = db.Column(db.Text,          nullable=False)
    keywords        = db.Column(db.String(500),   nullable=True)
    content         = db.Column(db.Text,          nullable=True)
    pdf_url         = db.Column(db.String(500),   nullable=True)

    # Co-authors (comma separated names)
    co_authors      = db.Column(db.String(500),   nullable=True)

    # Category/field
    category        = db.Column(db.String(200),   nullable=True)

    # Status workflow
    # draft → submitted → under_review → accepted → rejected → published
    status          = db.Column(db.String(50), default='draft')

    # Review feedback
    review_notes    = db.Column(db.Text,  nullable=True)
    editor_notes    = db.Column(db.Text,  nullable=True)

    # DOI
    doi             = db.Column(db.String(200), nullable=True, unique=True)

    # View count
    views           = db.Column(db.Integer, default=0)

    # Timestamps
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at    = db.Column(db.DateTime, nullable=True)
    published_at    = db.Column(db.DateTime, nullable=True)

    # Relationships
    author          = db.relationship('User', foreign_keys=[author_id],   backref='articles')
    reviewer        = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewing')
    editor          = db.relationship('User', foreign_keys=[editor_id],   backref='edited')
    tenant          = db.relationship('Tenant', backref='articles')

    # ── Helpers ──────────────────────────────────
    @property
    def status_badge(self):
        badges = {
            'draft':        'neutral',
            'submitted':    'info',
            'under_review': 'warning',
            'accepted':     'success',
            'rejected':     'danger',
            'published':    'success',
        }
        return badges.get(self.status, 'neutral')

    @property
    def status_label(self):
        return self.status.replace('_', ' ').title()

    @property
    def keyword_list(self):
        if self.keywords:
            return [k.strip() for k in self.keywords.split(',')]
        return []

    def increment_views(self):
        self.views += 1
        db.session.commit()

    def generate_doi(self):
        """Generate a simple DOI"""
        if not self.doi:
            self.doi = f'10.9999/rh.{self.tenant_id}.{self.id}'
            db.session.commit()

    def __repr__(self):
        return f'<Article {self.title[:50]} [{self.status}]>'