"""
Journal submission and review routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.journal import Journal, Submission, Article, Review
from app.utils.decorators import tenant_required, role_required
from app.utils.helpers import save_file, allowed_file
from datetime import datetime
from werkzeug.utils import secure_filename

journal_bp = Blueprint('journal', __name__)


@journal_bp.route('/')
@login_required
@tenant_required
def index():
    """List all journals"""
    journals = Journal.query.filter_by(tenant_id=request.tenant.id)\
        .order_by(Journal.created_at.desc()).all()
    
    return render_template('journal/index.html', journals=journals)


@journal_bp.route('/create', methods=['GET', 'POST'])
@login_required
@tenant_required
@role_required('admin', 'editor')
def create_journal():
    """Create new journal"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        submission_guidelines = request.form.get('submission_guidelines', '').strip()
        
        # Check tenant journal limit
        if not request.tenant.can_add_journal():
            flash('Journal limit reached. Please upgrade your plan.', 'warning')
            return redirect(url_for('journal.index'))
        
        journal = Journal(
            tenant_id=request.tenant.id,
            name=name,
            description=description,
            submission_guidelines=submission_guidelines,
            is_active=True,
            is_accepting_submissions=True
        )
        journal.generate_slug()
        
        db.session.add(journal)
        db.session.commit()
        
        flash('Journal created successfully!', 'success')
        return redirect(url_for('journal.view', journal_id=journal.id))
    
    return render_template('journal/create.html')


@journal_bp.route('/<int:journal_id>')
@login_required
@tenant_required
def view(journal_id):
    """View journal details"""
    journal = Journal.query.filter_by(
        id=journal_id,
        tenant_id=request.tenant.id
    ).first_or_404()
    
    # Get recent submissions
    submissions = Submission.query.filter_by(journal_id=journal_id)\
        .order_by(Submission.submitted_at.desc())\
        .limit(10).all()
    
    return render_template('journal/view.html', 
                         journal=journal, 
                         submissions=submissions)


@journal_bp.route('/<int:journal_id>/submit', methods=['GET', 'POST'])
@login_required
@tenant_required
def submit(journal_id):
    """Submit manuscript to journal"""
    journal = Journal.query.filter_by(
        id=journal_id,
        tenant_id=request.tenant.id
    ).first_or_404()
    
    if not journal.is_accepting_submissions:
        flash('This journal is not currently accepting submissions', 'warning')
        return redirect(url_for('journal.view', journal_id=journal_id))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        abstract = request.form.get('abstract', '').strip()
        keywords = request.form.get('keywords', '').strip().split(',')
        keywords = [k.strip() for k in keywords if k.strip()]
        
        # Get manuscript file
        manuscript_file = request.files.get('manuscript')
        if not manuscript_file or not allowed_file(manuscript_file.filename):
            flash('Please upload a valid manuscript file', 'danger')
            return render_template('journal/submit.html', journal=journal)
        
        # Save file
        file_path = save_file(manuscript_file, f'manuscripts/{journal_id}')
        
        # Create submission
        submission = Submission(
            journal_id=journal_id,
            user_id=current_user.id,
            title=title,
            abstract=abstract,
            keywords=keywords,
            manuscript_file_url=file_path,
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
@tenant_required
def my_submissions():
    """View user's submissions"""
    page = request.args.get('page', 1, type=int)
    
    submissions = Submission.query.filter_by(user_id=current_user.id)\
        .order_by(Submission.submitted_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('journal/my_submissions.html', submissions=submissions)


@journal_bp.route('/submission/<int:submission_id>')
@login_required
@tenant_required
def view_submission(submission_id):
    """View submission details"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Check access
    if submission.user_id != current_user.id and \
       not current_user.has_role('editor') and \
       not current_user.has_role('admin'):
        flash('Access denied', 'danger')
        return redirect(url_for('journal.my_submissions'))
    
    return render_template('journal/view_submission.html', submission=submission)


@journal_bp.route('/submission/<int:submission_id>/assign-reviewer', methods=['POST'])
@login_required
@tenant_required
@role_required('editor', 'admin')
def assign_reviewer(submission_id):
    """Assign reviewer to submission"""
    submission = Submission.query.get_or_404(submission_id)
    reviewer_id = request.form.get('reviewer_id', type=int)
    
    reviewer = User.query.get(reviewer_id)
    if not reviewer:
        flash('Reviewer not found', 'danger')
        return redirect(url_for('journal.view_submission', submission_id=submission_id))
    
    # Create review
    review = Review(
        submission_id=submission_id,
        reviewer_id=reviewer_id,
        status='invited',
        invited_at=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14)
    )
    
    db.session.add(review)
    
    # Update submission status
    submission.status = 'under_review'
    
    db.session.commit()
    
    flash('Reviewer assigned successfully!', 'success')
    return redirect(url_for('journal.view_submission', submission_id=submission_id))


@journal_bp.route('/review/<int:review_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def submit_review(review_id):
    """Submit peer review"""
    review = Review.query.get_or_404(review_id)
    
    # Check access
    if review.reviewer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('journal.index'))
    
    if request.method == 'POST':
        review.comments_to_author = request.form.get('comments_to_author', '')
        review.comments_to_editor = request.form.get('comments_to_editor', '')
        review.originality_rating = request.form.get('originality_rating', type=int)
        review.methodology_rating = request.form.get('methodology_rating', type=int)
        review.clarity_rating = request.form.get('clarity_rating', type=int)
        review.significance_rating = request.form.get('significance_rating', type=int)
        review.recommendation = request.form.get('recommendation')
        review.status = 'completed'
        review.submitted_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('journal.my_reviews'))
    
    return render_template('journal/submit_review.html', review=review)


@journal_bp.route('/my-reviews')
@login_required
@tenant_required
def my_reviews():
    """View user's reviews"""
    page = request.args.get('page', 1, type=int)
    
    reviews = Review.query.filter_by(reviewer_id=current_user.id)\
        .order_by(Review.invited_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('journal/my_reviews.html', reviews=reviews)


@journal_bp.route('/submission/<int:submission_id>/decision', methods=['POST'])
@login_required
@tenant_required
@role_required('editor', 'admin')
def editorial_decision(submission_id):
    """Make editorial decision"""
    submission = Submission.query.get_or_404(submission_id)
    
    decision = request.form.get('decision')
    editor_notes = request.form.get('editor_notes', '')
    
    submission.status = decision
    submission.editor_notes = editor_notes
    submission.decision_date = datetime.utcnow()
    
    # If accepted, create article
    if decision == 'accepted':
        article = Article(
            journal_id=submission.journal_id,
            submission_id=submission.id,
            title=submission.title,
            abstract=submission.abstract,
            keywords=submission.keywords,
            authors=submission.authors,
            is_published=False
        )
        article.generate_slug()
        db.session.add(article)
    
    db.session.commit()
    
    flash('Editorial decision recorded!', 'success')
    return redirect(url_for('journal.view_submission', submission_id=submission_id))