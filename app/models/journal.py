"""
Journal, Submission, and Review models
"""
from datetime import datetime, timedelta
from app.extensions import db

class Journal(db.Model):
    """Journal/Publication model"""
    
    __tablename__ = 'journals'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Basic Info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_accepting_submissions = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='journal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Journal {self.name}>'

class Submission(db.Model):
    """Manuscript submission model"""
    
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    
    # Files
    manuscript_file_url = db.Column(db.String(500), nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='submitted')
    # Possible: submitted, under_review, accepted, rejected
    
    # Dates
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='submissions')
    reviews = db.relationship('Review', backref='submission', lazy='dynamic')
    
    def __repr__(self):
        return f'<Submission {self.title}>'

class Review(db.Model):
    """Peer review model"""
    
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review content
    comments = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)  # 1-5
    
    # Recommendation
    recommendation = db.Column(db.String(50), nullable=True)
    # Possible: accept, minor_revision, major_revision, reject
    
    # Status
    status = db.Column(db.String(50), default='pending')
    # Possible: pending, completed
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reviewer = db.relationship('User', backref='reviews')
    
    def __repr__(self):
        return f'<Review {self.id}>'