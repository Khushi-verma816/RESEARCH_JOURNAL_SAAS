"""
Phase 4: Admin Dashboard & Review Management
"""
import os

def create_file(path, content):
    """Create a file with content"""
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

files = {
    'app/routes/admin.py': '''"""
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
''',

    'app/templates/admin/dashboard.html': '''{% extends "base.html" %}

{% block title %}Admin Dashboard - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 25px;">🎛️ Admin Dashboard</h1>
    
    <!-- Statistics Cards -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 8px; color: white;">
            <h3 style="margin: 0; font-size: 36px;">{{ total_journals }}</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Total Journals</p>
        </div>
        
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px; border-radius: 8px; color: white;">
            <h3 style="margin: 0; font-size: 36px;">{{ total_submissions }}</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Total Submissions</p>
        </div>
        
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 25px; border-radius: 8px; color: white;">
            <h3 style="margin: 0; font-size: 36px;">{{ pending_submissions }}</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Pending Review</p>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div style="margin-bottom: 30px;">
        <h2 style="color: #333; margin-bottom: 15px;">Quick Actions</h2>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="{{ url_for('admin.submissions') }}" 
               style="padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 6px;">
                📋 Manage Submissions
            </a>
            <a href="{{ url_for('journal.create') }}" 
               style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px;">
                ➕ Create Journal
            </a>
            <a href="{{ url_for('admin.users') }}" 
               style="padding: 12px 24px; background: #6f42c1; color: white; text-decoration: none; border-radius: 6px;">
                👥 Manage Users
            </a>
        </div>
    </div>
    
    <!-- Recent Submissions -->
    <h2 style="color: #333; margin-bottom: 15px;">Recent Submissions</h2>
    {% if recent_submissions %}
        <div style="display: grid; gap: 15px;">
            {% for submission in recent_submissions %}
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 8px 0; color: #333;">{{ submission.title }}</h4>
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        <strong>Author:</strong> {{ submission.author.full_name }} | 
                        <strong>Journal:</strong> {{ submission.journal.name }}
                    </p>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    {% if submission.status == 'submitted' %}
                        <span style="background: #007bff; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">SUBMITTED</span>
                    {% elif submission.status == 'under_review' %}
                        <span style="background: #ffc107; color: #333; padding: 6px 12px; border-radius: 12px; font-size: 12px;">UNDER REVIEW</span>
                    {% elif submission.status == 'accepted' %}
                        <span style="background: #28a745; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">ACCEPTED</span>
                    {% elif submission.status == 'rejected' %}
                        <span style="background: #dc3545; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">REJECTED</span>
                    {% endif %}
                    <a href="{{ url_for('admin.manage_submission', submission_id=submission.id) }}" 
                       style="padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">
                        Manage
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #666; text-align: center; padding: 40px; background: #f8f9fa; border-radius: 6px;">
            No submissions yet.
        </p>
    {% endif %}
</div>
{% endblock %}
''',

    'app/templates/admin/submissions.html': '''{% extends "base.html" %}

{% block title %}Manage Submissions - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 25px;">📋 Manage Submissions</h1>
    
    <!-- Filter -->
    <div style="margin-bottom: 20px; display: flex; gap: 10px;">
        <a href="{{ url_for('admin.submissions', status='all') }}" 
           style="padding: 8px 16px; background: {% if status_filter == 'all' %}#007bff{% else %}#e9ecef{% endif %}; 
                  color: {% if status_filter == 'all' %}white{% else %}#333{% endif %}; 
                  text-decoration: none; border-radius: 4px;">
            All
        </a>
        <a href="{{ url_for('admin.submissions', status='submitted') }}" 
           style="padding: 8px 16px; background: {% if status_filter == 'submitted' %}#007bff{% else %}#e9ecef{% endif %}; 
                  color: {% if status_filter == 'submitted' %}white{% else %}#333{% endif %}; 
                  text-decoration: none; border-radius: 4px;">
            Submitted
        </a>
        <a href="{{ url_for('admin.submissions', status='under_review') }}" 
           style="padding: 8px 16px; background: {% if status_filter == 'under_review' %}#ffc107{% else %}#e9ecef{% endif %}; 
                  color: {% if status_filter == 'under_review' %}#333{% else %}#333{% endif %}; 
                  text-decoration: none; border-radius: 4px;">
            Under Review
        </a>
        <a href="{{ url_for('admin.submissions', status='accepted') }}" 
           style="padding: 8px 16px; background: {% if status_filter == 'accepted' %}#28a745{% else %}#e9ecef{% endif %}; 
                  color: {% if status_filter == 'accepted' %}white{% else %}#333{% endif %}; 
                  text-decoration: none; border-radius: 4px;">
            Accepted
        </a>
        <a href="{{ url_for('admin.submissions', status='rejected') }}" 
           style="padding: 8px 16px; background: {% if status_filter == 'rejected' %}#dc3545{% else %}#e9ecef{% endif %}; 
                  color: {% if status_filter == 'rejected' %}white{% else %}#333{% endif %}; 
                  text-decoration: none; border-radius: 4px;">
            Rejected
        </a>
    </div>
    
    <!-- Submissions List -->
    {% if submissions %}
        <div style="display: grid; gap: 15px;">
            {% for submission in submissions %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{{ submission.title }}</h3>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>Author:</strong> {{ submission.author.full_name }} ({{ submission.author.email }})
                        </p>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>Journal:</strong> {{ submission.journal.name }}
                        </p>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y at %I:%M %p') }}
                        </p>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 10px; align-items: flex-end;">
                        {% if submission.status == 'submitted' %}
                            <span style="background: #007bff; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">SUBMITTED</span>
                        {% elif submission.status == 'under_review' %}
                            <span style="background: #ffc107; color: #333; padding: 6px 12px; border-radius: 12px; font-size: 12px;">UNDER REVIEW</span>
                        {% elif submission.status == 'accepted' %}
                            <span style="background: #28a745; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">ACCEPTED</span>
                        {% elif submission.status == 'rejected' %}
                            <span style="background: #dc3545; color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px;">REJECTED</span>
                        {% endif %}
                        <a href="{{ url_for('admin.manage_submission', submission_id=submission.id) }}" 
                           style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                            Manage
                        </a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #666; text-align: center; padding: 40px; background: #f8f9fa; border-radius: 6px;">
            No submissions found for this filter.
        </p>
    {% endif %}
</div>
{% endblock %}
''',

    'app/templates/admin/manage_submission.html': '''{% extends "base.html" %}

{% block title %}Manage {{ submission.title }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 20px;">Manage Submission</h1>
    
    <!-- Submission Details -->
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 30px;">
        <h2 style="color: #333; margin-top: 0;">{{ submission.title }}</h2>
        <p style="color: #666; margin: 5px 0;"><strong>Author:</strong> {{ submission.author.full_name }} ({{ submission.author.email }})</p>
        <p style="color: #666; margin: 5px 0;"><strong>Journal:</strong> {{ submission.journal.name }}</p>
        <p style="color: #666; margin: 5px 0;"><strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y at %I:%M %p') }}</p>
        <p style="color: #666; margin: 5px 0;">
            <strong>Status:</strong> 
            {% if submission.status == 'submitted' %}
                <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">SUBMITTED</span>
            {% elif submission.status == 'under_review' %}
                <span style="background: #ffc107; color: #333; padding: 4px 12px; border-radius: 12px; font-size: 12px;">UNDER REVIEW</span>
            {% elif submission.status == 'accepted' %}
                <span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">ACCEPTED</span>
            {% elif submission.status == 'rejected' %}
                <span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">REJECTED</span>
            {% endif %}
        </p>
    </div>
    
    <!-- Abstract -->
    <div style="margin-bottom: 30px;">
        <h3 style="color: #333;">Abstract</h3>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; line-height: 1.6;">
            <p style="color: #333;">{{ submission.abstract }}</p>
        </div>
    </div>
    
    <!-- Change Status -->
    <div style="margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 6px;">
        <h3 style="color: #333; margin-top: 0;">Change Status</h3>
        <form method="POST" style="display: flex; gap: 10px; align-items: center;">
            <input type="hidden" name="action" value="change_status">
            <select name="status" style="padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px;">
                <option value="submitted" {% if submission.status == 'submitted' %}selected{% endif %}>Submitted</option>
                <option value="under_review" {% if submission.status == 'under_review' %}selected{% endif %}>Under Review</option>
                <option value="accepted" {% if submission.status == 'accepted' %}selected{% endif %}>Accepted</option>
                <option value="rejected" {% if submission.status == 'rejected' %}selected{% endif %}>Rejected</option>
            </select>
            <button type="submit" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Update Status
            </button>
        </form>
    </div>
    
    <!-- Assign Reviewer -->
    <div style="margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 6px;">
        <h3 style="color: #333; margin-top: 0;">Assign Reviewer</h3>
        {% if reviewers %}
            <form method="POST" style="display: flex; gap: 10px; align-items: center;">
                <input type="hidden" name="action" value="assign_reviewer">
                <select name="reviewer_id" style="padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px;">
                    <option value="">Select Reviewer</option>
                    {% for reviewer in reviewers %}
                        <option value="{{ reviewer.id }}">{{ reviewer.full_name }} ({{ reviewer.email }})</option>
                    {% endfor %}
                </select>
                <button type="submit" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Assign Reviewer
                </button>
            </form>
        {% else %}
            <p style="color: #666;">No reviewers available. Please assign the "reviewer" role to users first.</p>
        {% endif %}
    </div>
    
    <!-- Assigned Reviews -->
    <div style="margin-bottom: 30px;">
        <h3 style="color: #333;">Assigned Reviews ({{ reviews|length }})</h3>
        {% if reviews %}
            <div style="display: grid; gap: 15px;">
                {% for review in reviews %}
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 6px;">
                    <p style="margin: 5px 0; color: #333;"><strong>Reviewer:</strong> {{ review.reviewer.full_name }}</p>
                    <p style="margin: 5px 0; color: #666;"><strong>Status:</strong> 
                        <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">
                            {{ review.status|upper }}
                        </span>
                    </p>
                    <p style="margin: 5px 0; color: #666;"><strong>Assigned:</strong> {{ review.created_at.strftime('%B %d, %Y') }}</p>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <p style="color: #666; padding: 20px; background: #f8f9fa; border-radius: 6px;">No reviews assigned yet.</p>
        {% endif %}
    </div>
    
    <a href="{{ url_for('admin.submissions') }}" 
       style="padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">
        ← Back to Submissions
    </a>
</div>
{% endblock %}
''',

    'app/templates/admin/users.html': '''{% extends "base.html" %}

{% block title %}Manage Users - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 25px;">👥 Manage Users</h1>
    
    <div style="display: grid; gap: 15px;">
        {% for user in users %}
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">{{ user.full_name }}</h3>
                    <p style="margin: 5px 0; color: #666;"><strong>Email:</strong> {{ user.email }}</p>
                    <p style="margin: 5px 0; color: #666;">
                        <strong>Roles:</strong>
                        {% if user.roles %}
                            {% for role in user.roles %}
                                <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px;">
                                    {{ role.name|upper }}
                                </span>
                            {% endfor %}
                        {% else %}
                            <span style="color: #999;">No roles</span>
                        {% endif %}
                    </p>
                </div>
                <div>
                    <form method="POST" action="{{ url_for('admin.assign_role', user_id=user.id) }}" style="display: flex; gap: 10px;">
                        <select name="role_id" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="">Assign Role</option>
                            {% for role in roles %}
                                <option value="{{ role.id }}">{{ role.name }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Assign
                        </button>
                    </form>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
''',
}

print("Creating Phase 4 files...\n")
for filepath, content in files.items():
    create_file(filepath, content)

print("\n" + "="*60)
print("✅ PHASE 4 FILES CREATED SUCCESSFULLY!")
print("="*60)
print("\nNext steps:")
print("1. Update app/__init__.py to register admin blueprint")
print("2. Update navigation to add Admin link")
print("3. Restart Flask")
print("4. Test the admin dashboard!")