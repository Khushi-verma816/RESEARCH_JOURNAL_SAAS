"""
User Profile routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Submission, BlogPost, AIConversation
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
@login_required
def index():
    """User profile page"""

    # Submission stats
    submissions_count = Submission.query.filter_by(
        user_id=current_user.id
    ).count()

    accepted_count = Submission.query.filter_by(
        user_id=current_user.id,
        status='accepted'
    ).count()

    # ✅ FIXED: BlogPost uses author_id
    blog_count = BlogPost.query.filter_by(
        author_id=current_user.id
    ).count()

    # AI conversations
    try:
        ai_count = AIConversation.query.filter_by(
            user_id=current_user.id
        ).count()
    except Exception:
        ai_count = 0

    # Recent submissions
    recent_submissions = Submission.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Submission.submitted_at.desc()
    ).limit(5).all()

    stats = {
        'submissions': submissions_count,
        'accepted': accepted_count,
        'blogs': blog_count,
        'ai_chats': ai_count
    }

    return render_template(
        'profile/index.html',
        stats=stats,
        recent_submissions=recent_submissions
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit profile"""

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        if not first_name or not last_name:
            flash('Name fields are required', 'danger')
            return render_template('profile/edit.html')

        current_user.first_name = first_name
        current_user.last_name = last_name
        db.session.commit()

        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile/edit.html')


@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        stored_password = getattr(
            current_user, 'password_hash', None
        ) or getattr(current_user, 'password', None)

        if not stored_password or not check_password_hash(
            stored_password, current_password
        ):
            flash('❌ Current password is incorrect', 'danger')
            return render_template('profile/change_password.html')

        if len(new_password) < 6:
            flash('❌ New password must be at least 6 characters', 'danger')
            return render_template('profile/change_password.html')

        if new_password != confirm_password:
            flash('❌ Passwords do not match', 'danger')
            return render_template('profile/change_password.html')

        hashed = generate_password_hash(new_password)

        if hasattr(current_user, 'password_hash'):
            current_user.password_hash = hashed
        else:
            current_user.password = hashed

        db.session.commit()

        flash('✅ Password changed successfully!', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile/change_password.html')
