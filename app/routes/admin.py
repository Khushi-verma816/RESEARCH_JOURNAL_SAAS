"""
Admin dashboard routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Journal, Submission, Review, User, Role
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('admin') and not current_user.has_role('editor'):
            flash('Access denied. Admin or Editor role required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_journals = Journal.query.filter_by(tenant_id=current_user.tenant_id).count()
    total_submissions = Submission.query.join(Journal).filter(
        Journal.tenant_id == current_user.tenant_id
    ).count()
    pending_submissions = Submission.query.join(Journal).filter(
        Journal.tenant_id == current_user.tenant_id,
        Submission.status == 'submitted'
    ).count()
    
    # Get recent submissions
    recent_submissions = Submission.query.join(Journal).filter(
        Journal.tenant_id == current_user.tenant_id
    ).order_by(Submission.submitted_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_journals=total_journals,
                         total_submissions=total_submissions,
                         pending_submissions=pending_submissions,
                         recent_submissions=recent_submissions)

@admin_bp.route('/submissions')
@login_required
@admin_required
def submissions():
    """View all submissions"""
    status_filter = request.args.get('status', 'all')
    
    query = Submission.query.join(Journal).filter(
        Journal.tenant_id == current_user.tenant_id
    )
    
    if status_filter != 'all':
        query = query.filter(Submission.status == status_filter)
    
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    
    return render_template('admin/submissions.html', 
                         submissions=submissions,
                         status_filter=status_filter)

@admin_bp.route('/submission/<int:submission_id>/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_submission(submission_id):
    """Manage a submission"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Verify access
    if submission.journal.tenant_id != current_user.tenant_id:
        flash('Access denied', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_status':
            new_status = request.form.get('status')
            if new_status in ['submitted', 'under_review', 'accepted', 'rejected']:
                submission.status = new_status
                db.session.commit()
                flash(f'Submission status changed to {new_status}', 'success')
        
        elif action == 'assign_reviewer':
            reviewer_id = request.form.get('reviewer_id')
            if reviewer_id:
                # Create review assignment
                review = Review(
                    submission_id=submission_id,
                    reviewer_id=int(reviewer_id),
                    status='pending'
                )
                db.session.add(review)
                submission.status = 'under_review'
                db.session.commit()
                flash('Reviewer assigned successfully', 'success')
        
        return redirect(url_for('admin.manage_submission', submission_id=submission_id))
    
    # Get potential reviewers (users with reviewer role)
    reviewer_role = Role.query.filter_by(name='reviewer').first()
    reviewers = User.query.filter(
        User.tenant_id == current_user.tenant_id,
        User.roles.contains(reviewer_role)
    ).all() if reviewer_role else []
    
    # Get assigned reviews
    reviews = Review.query.filter_by(submission_id=submission_id).all()
    
    return render_template('admin/manage_submission.html',
                         submission=submission,
                         reviewers=reviewers,
                         reviews=reviews)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    users = User.query.filter_by(tenant_id=current_user.tenant_id).all()
    roles = Role.query.all()
    
    return render_template('admin/users.html', users=users, roles=roles)

@admin_bp.route('/user/<int:user_id>/assign-role', methods=['POST'])
@login_required
@admin_required
def assign_role(user_id):
    """Assign role to user"""
    user = User.query.get_or_404(user_id)
    
    if user.tenant_id != current_user.tenant_id:
        flash('Access denied', 'danger')
        return redirect(url_for('admin.users'))
    
    role_id = request.form.get('role_id')
    role = Role.query.get(role_id)
    
    if role and role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        flash(f'Role {role.name} assigned to {user.email}', 'success')
    
    return redirect(url_for('admin.users'))
