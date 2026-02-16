"""
Journal management routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Journal, Submission, Review
from datetime import datetime

journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/')
@login_required
def index():
    """List all journals"""
    journals = Journal.query.filter_by(is_active=True).all()
    return render_template('journal/submit_with_upload.html', journal=journal)
@journal_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new journal"""
    # Check if user has admin or editor role
    if not (current_user.has_role('admin') or current_user.has_role('editor')):
        flash('You do not have permission to create journals', 'danger')
        return redirect(url_for('journal.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Journal name is required', 'danger')
            return render_template('journal/create.html')
        
        journal = Journal(
            tenant_id=current_user.tenant_id,
            name=name,
            description=description,
            is_active=True,
            is_accepting_submissions=True
        )
        
        db.session.add(journal)
        db.session.commit()
        
        flash(f'Journal "{name}" created successfully!', 'success')
        return redirect(url_for('journal.view', journal_id=journal.id))
    
    return render_template('journal/create.html')

@journal_bp.route('/<int:journal_id>')
@login_required
def view(journal_id):
    """View journal details"""
    journal = Journal.query.get_or_404(journal_id)
    
    # Get recent submissions for this journal
    submissions = Submission.query.filter_by(journal_id=journal_id)\
        .order_by(Submission.submitted_at.desc())\
        .limit(10).all()
    
    return render_template('journal/view.html', journal=journal, submissions=submissions)

@journal_bp.route('/<int:journal_id>/submit', methods=['GET', 'POST'])
@login_required
def submit(journal_id):
    """Submit manuscript to journal"""
    journal = Journal.query.get_or_404(journal_id)
    
    if not journal.is_accepting_submissions:
        flash('This journal is not currently accepting submissions', 'warning')
        return redirect(url_for('journal.view', journal_id=journal_id))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        abstract = request.form.get('abstract', '').strip()
        
        if not title or not abstract:
            flash('Title and abstract are required', 'danger')
            return render_template('journal/submit.html', journal=journal)
        
        submission = Submission(
            journal_id=journal_id,
            user_id=current_user.id,
            title=title,
            abstract=abstract,
            manuscript_file_url='placeholder.pdf',
            status='submitted',
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Manuscript submitted successfully!', 'success')
        return redirect(url_for('journal.my_submissions'))
    
    return render_template('journal/submit.html', journal=journal)

@journal_bp.route('/my-submissions')
@login_required
def my_submissions():
    """View user's submissions"""
    submissions = Submission.query.filter_by(user_id=current_user.id)\
        .order_by(Submission.submitted_at.desc()).all()
    
    return render_template('journal/my_submissions.html', submissions=submissions)

@journal_bp.route('/submission/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """View submission details"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Check access
    can_view = (
        submission.user_id == current_user.id or
        current_user.has_role('admin') or
        current_user.has_role('editor')
    )
    
    if not can_view:
        flash('Access denied', 'danger')
        return redirect(url_for('journal.my_submissions'))
    
    reviews = Review.query.filter_by(submission_id=submission_id).all()
    
    return render_template('journal/view_submission.html', 
                         submission=submission, 
                         reviews=reviews)

@journal_bp.route('/my-reviews')
@login_required
def my_reviews():
    """View user's assigned reviews"""
    reviews = Review.query.filter_by(reviewer_id=current_user.id)\
        .order_by(Review.created_at.desc()).all()
    
    return render_template('journal/my_reviews.html', reviews=reviews)