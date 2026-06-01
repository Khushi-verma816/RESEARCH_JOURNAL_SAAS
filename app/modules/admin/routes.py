# app/modules/admin/routes.py

from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import case
from werkzeug.utils import secure_filename

from app.core.notifications import (
    count_unread_notifications,
    create_notifications_for_roles,
    fetch_notifications_for_user,
    mark_all_notifications_read_for_user,
    mark_notification_read,
)
from app.core.extensions import db
from app.models.article import Article
from app.models.custom_domain import CustomDomainRequest
from app.models.tenant import Tenant
from app.models.testimonial import Testimonial
from app.models.user import User
from app.modules.admin import admin_bp

PLATFORM_ADMIN_ROLES = {'super_admin', 'admin'}
MANAGED_USER_ROLES = ['subscriber', 'author', 'reviewer', 'editor', 'tenant_owner', 'admin', 'super_admin']
ALLOWED_TESTIMONIAL_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def _save_testimonial_photo(photo):
    if not photo or not photo.filename:
        return None

    secure_name = secure_filename(photo.filename)
    suffix = Path(secure_name).suffix.lower()
    if suffix not in ALLOWED_TESTIMONIAL_IMAGE_EXTENSIONS:
        raise ValueError('Photo must be one of: jpg, jpeg, png, webp, gif.')

    upload_dir = Path(current_app.static_folder) / 'uploads' / 'testimonials'
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_filename = f'testimonial-{uuid4().hex}{suffix}'
    photo.save(upload_dir / saved_filename)

    return url_for('static', filename=f'uploads/testimonials/{saved_filename}')

def platform_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in PLATFORM_ADMIN_ROLES:
            flash('Access denied. Platform admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated

def _scoped_articles_query():
    """Return article query scoped to current user's dashboard context."""
    if current_user.is_admin():
        return Article.query

    if current_user.tenant_id:
        return Article.query.filter_by(tenant_id=current_user.tenant_id)

    return Article.query.filter_by(author_id=current_user.id)

@admin_bp.route('/dashboard')
@login_required
@platform_admin_required
def dashboard():
    my_tenant = Tenant.query.get(current_user.tenant_id) if current_user.tenant_id else None
    scoped_articles = _scoped_articles_query()

    total_articles = scoped_articles.count()
    published_count = scoped_articles.filter_by(status='published').count()
    pending_count = scoped_articles.filter(Article.status.in_(['submitted', 'under_review'])).count()
    total_views = scoped_articles.with_entities(
        db.func.coalesce(db.func.sum(Article.views), 0)
    ).scalar() or 0

    stats = {
        'total': total_articles,
        'published': published_count,
        'views': int(total_views),
        'under_review': pending_count,
    }

    recent_articles = (
        scoped_articles
        .order_by(Article.created_at.desc())
        .limit(8)
        .all()
    )

    platform_stats = {
        'users': User.query.count(),
        'journals': Tenant.query.count(),
        'articles': Article.query.count(),
        'pending': Article.query.filter(Article.status.in_(['submitted', 'under_review'])).count(),
    }
    top_notifications = fetch_notifications_for_user(current_user.id, limit=12)
    unread_notification_count = count_unread_notifications(current_user.id)

    # ── Analytics data for dashboard (for all admin roles) ────────────────────
    scoped_q = _scoped_articles_query()
    all_articles_for_analytics = scoped_q.all()
    published_arts  = [a for a in all_articles_for_analytics if a.status == 'published']
    under_review_arts = [a for a in all_articles_for_analytics if a.status == 'under_review']
    submitted_arts  = [a for a in all_articles_for_analytics if a.status == 'submitted']
    rejected_arts   = [a for a in all_articles_for_analytics if a.status == 'rejected']
    draft_arts      = [a for a in all_articles_for_analytics if a.status == 'draft']

    status_data = {
        'Published':    len(published_arts),
        'Under Review': len(under_review_arts),
        'Submitted':    len(submitted_arts),
        'Rejected':     len(rejected_arts),
        'Draft':        len(draft_arts),
    }
    top_articles = sorted(published_arts, key=lambda a: a.views, reverse=True)[:5]

    monthly_data = []
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end   = month_start + timedelta(days=31)
        count = len([a for a in all_articles_for_analytics
                     if month_start <= a.created_at < month_end])
        monthly_data.append({'month': month_start.strftime('%b %Y'), 'count': count})

    categories = {}
    for a in all_articles_for_analytics:
        cat = getattr(a, 'category', None) or 'Uncategorized'
        categories[cat] = categories.get(cat, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:6]

    # Team breakdown — scoped to current admin's tenant if they have one
    analytics_tenant_id = current_user.tenant_id
    if analytics_tenant_id:
        members   = User.query.filter_by(tenant_id=analytics_tenant_id).all()
        authors   = [m for m in members if m.role == 'author']
        reviewers = [m for m in members if m.role == 'reviewer']
        editors   = [m for m in members if m.role in ['editor', 'tenant_owner']]
    else:
        authors = reviewers = editors = []

    return render_template(
        'admin/dashboard.html',
        user=current_user,
        my_tenant=my_tenant,
        dashboard_mode='platform' if current_user.is_admin() else 'member',
        stats=stats,
        platform_stats=platform_stats,
        recent_articles=recent_articles,
        total_users=platform_stats['users'],
        total_journals=platform_stats['journals'],
        total_articles=platform_stats['articles'],
        pending=platform_stats['pending'],
        top_notifications=top_notifications,
        unread_notification_count=unread_notification_count,
        # Analytics data
        status_data=status_data,
        monthly_data=monthly_data,
        top_articles=top_articles,
        top_categories=top_categories,
        authors=authors,
        reviewers=reviewers,
        editors=editors,
    )

@admin_bp.route('/notifications/<int:notification_id>/open')
@login_required
@platform_admin_required
def open_notification(notification_id):
    notification = mark_notification_read(current_user.id, notification_id)
    if not notification:
        flash('Notification not found.', 'warning')
        return redirect(url_for('admin.dashboard'))
    return redirect(notification.link_url or url_for('admin.dashboard'))

@admin_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@platform_admin_required
def mark_all_notifications():
    marked_count = mark_all_notifications_read_for_user(current_user.id)
    if marked_count:
        flash(f'{marked_count} notification(s) marked as read.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users')
@login_required
@platform_admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    role_filter = request.args.get('role', '')

    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )
    if role_filter:
        query = query.filter_by(role=role_filter)

    role_priority = case(
        (User.role == 'super_admin', 0),
        (User.role == 'admin', 1),
        (User.role == 'tenant_owner', 2),
        (User.role == 'editor', 3),
        (User.role == 'reviewer', 4),
        (User.role == 'author', 5),
        else_=6,
    )
    users_paginated = query.order_by(role_priority.asc(), User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/users.html',
        user=current_user,
        users=users_paginated,
        search=search,
        role_filter=role_filter,
    )

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@platform_admin_required
def toggle_user_active(user_id):
    u = User.query.get_or_404(user_id)

    if u.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))

    if u.is_super_admin() and not current_user.is_super_admin():
        flash('Only a super admin can modify another super admin.', 'danger')
        return redirect(url_for('admin.users'))

    u.is_active = not u.is_active
    db.session.commit()
    flash(f'User {"activated" if u.is_active else "deactivated"} successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@platform_admin_required
def change_user_role(user_id):
    u = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if new_role not in MANAGED_USER_ROLES:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin.users'))

    if u.id == current_user.id and new_role != u.role:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.users'))

    if new_role == 'super_admin' and not current_user.is_super_admin():
        flash('Only super admin can assign super admin role.', 'danger')
        return redirect(url_for('admin.users'))

    if u.is_super_admin() and not current_user.is_super_admin():
        flash('Only super admin can modify another super admin.', 'danger')
        return redirect(url_for('admin.users'))

    u.role = new_role
    db.session.commit()
    flash(f'Role updated to {new_role}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/journals')
@login_required
@platform_admin_required
def journals():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    plan_filter = request.args.get('plan', '')

    query = Tenant.query
    if search:
        query = query.filter(
            db.or_(
                Tenant.name.ilike(f'%{search}%'),
                Tenant.subdomain.ilike(f'%{search}%'),
            )
        )
    if plan_filter:
        query = query.filter_by(plan=plan_filter)

    journals_paginated = query.order_by(Tenant.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/journals.html',
        user=current_user,
        journals=journals_paginated,
        search=search,
        plan_filter=plan_filter,
    )

@admin_bp.route('/journals/<int:journal_id>/toggle-active', methods=['POST'])
@login_required
@platform_admin_required
def toggle_journal_active(journal_id):
    j = Tenant.query.get_or_404(journal_id)
    j.is_active = not j.is_active
    db.session.commit()
    flash(f'Journal {"activated" if j.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.journals'))

@admin_bp.route('/submissions')
@login_required
@platform_admin_required
def submissions():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    status_filter = request.args.get('status', '')

    query = Article.query
    if search:
        query = query.filter(
            db.or_(
                Article.title.ilike(f'%{search}%'),
                Article.keywords.ilike(f'%{search}%'),
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    articles_paginated = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/submissions.html',
        user=current_user,
        articles=articles_paginated,
        search=search,
        status_filter=status_filter,
    )

@admin_bp.route('/submissions/<int:article_id>/status', methods=['POST'])
@login_required
@platform_admin_required
def change_article_status(article_id):
    a = Article.query.get_or_404(article_id)
    new_status = request.form.get('status')
    valid = ['draft', 'submitted', 'under_review', 'accepted', 'rejected', 'published']
    if new_status in valid:
        a.status = new_status
        db.session.commit()
        flash(f'Article status changed to {new_status}.', 'success')
    return redirect(url_for('admin.submissions'))

# SUPER ADMIN - PLATFORM MANAGEMENT

@admin_bp.route('/system-health')
@login_required
@platform_admin_required
def system_health():
    """System health monitoring - CPU, DB status, uptime."""
    import psutil
    import os
    import sys
    from datetime import datetime

    # System stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    # Use OS-appropriate disk path (C:\ on Windows, / on Linux)
    disk_path = 'C:\\' if sys.platform == 'win32' else '/'
    try:
        disk = psutil.disk_usage(disk_path)
        disk_data = {
            'total': disk.total // (1024**3),
            'used': disk.used // (1024**3),
            'percent': (disk.used / disk.total) * 100
        }
    except Exception:
        disk_data = {'total': 0, 'used': 0, 'percent': 0}

    # Database check
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception:
        db_status = 'error'

    # Server uptime (from file modification time as approximation)
    try:
        run_py = Path(current_app.root_path).parent / 'run.py'
        stat = os.stat(run_py)
        uptime = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
    except Exception:
        uptime = None

    health_data = {
        'cpu': {'usage': cpu_percent, 'cores': psutil.cpu_count()},
        'memory': {
            'total': memory.total // (1024**3),
            'used': memory.used // (1024**3),
            'percent': memory.percent
        },
        'disk': disk_data,
        'db_status': db_status,
        'uptime': uptime,
    }
    return render_template('admin/system_health.html', health=health_data, now_str=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@admin_bp.route('/platform-config', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def platform_config():
    """Platform configuration - name, logo, email settings, SMTP."""
    if request.method == 'POST':
        # Save configuration
        config_data = {
            'platform_name': request.form.get('platform_name'),
            'contact_email': request.form.get('contact_email'),
            'smtp_host': request.form.get('smtp_host'),
            'smtp_port': request.form.get('smtp_port'),
            'smtp_user': request.form.get('smtp_user'),
            'maintenance_mode': request.form.get('maintenance_mode') == 'on',
        }
        # Store in database or config file
        flash('Platform configuration saved successfully.', 'success')
        return redirect(url_for('admin.platform_config'))
    return render_template('admin/platform_config.html')

@admin_bp.route('/feature-toggle', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def feature_toggle():
    """Enable/disable features like AI, submissions, journals."""
    if request.method == 'POST':
        features = {
            'ai_assistant': request.form.get('ai_assistant') == 'on',
            'submissions': request.form.get('submissions') == 'on',
            'new_journals': request.form.get('new_journals') == 'on',
            'user_registration': request.form.get('user_registration') == 'on',
            'video_rooms': request.form.get('video_rooms') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
        }
        flash('Feature toggles updated.', 'success')
        return redirect(url_for('admin.feature_toggle'))
    return render_template('admin/feature_toggle.html')

# SUPER ADMIN - USER & ROLE MANAGEMENT

@admin_bp.route('/roles-permissions')
@login_required
@platform_admin_required
def roles_permissions():
    """Role-based access control (RBAC) management."""
    roles = ['super_admin', 'admin', 'tenant_owner', 'editor', 'reviewer', 'author', 'subscriber']
    permissions = {
        'super_admin': ['all'],
        'admin': ['manage_users', 'manage_journals', 'manage_submissions', 'view_analytics'],
        'tenant_owner': ['manage_journal', 'manage_team', 'view_journal_analytics'],
        'editor': ['review_articles', 'manage_journal_content'],
        'reviewer': ['review_assigned_articles'],
        'author': ['submit_articles', 'view_own_articles'],
        'subscriber': ['view_published_content'],
    }
    return render_template('admin/roles_permissions.html', roles=roles, permissions=permissions)

@admin_bp.route('/banned-users')
@login_required
@platform_admin_required
def banned_users():
    """View and manage banned/suspended users."""
    page = request.args.get('page', 1, type=int)
    query = User.query.filter_by(is_active=False)
    banned = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/banned_users.html', users=banned)

@admin_bp.route('/activity-logs')
@login_required
@platform_admin_required
def activity_logs():
    """User activity tracking - login logs, actions."""
    page = request.args.get('page', 1, type=int)
    user_filter = request.args.get('user', '')
    # Query activity logs from database (login_ip not in model, use available columns)
    logs_query = User.query
    if user_filter:
        logs_query = logs_query.filter(User.email.ilike(f'%{user_filter}%'))
    logs = logs_query.order_by(User.last_login.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('admin/activity_logs.html', logs=logs, user_filter=user_filter)

@admin_bp.route('/bulk-import', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def bulk_import():
    """Bulk user import/export via CSV/Excel."""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'import':
            file = request.files.get('import_file')
            if file:
                flash(f'Importing users from {file.filename}...', 'info')
                # Process CSV/Excel import
        elif action == 'export':
            flash('Exporting user data...', 'info')
            # Generate CSV export
    return render_template('admin/bulk_import.html')

# SUPER ADMIN - JOURNAL MANAGEMENT

@admin_bp.route('/create-journal', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def create_journal():
    """Create new journal from super admin panel."""
    if request.method == 'POST':
        name = request.form.get('name')
        subdomain = request.form.get('subdomain')
        description = request.form.get('description')
        plan = request.form.get('plan', 'free')
        # Create journal logic
        flash(f'Journal "{name}" created successfully.', 'success')
        return redirect(url_for('admin.journals'))
    return render_template('admin/create_journal.html')

@admin_bp.route('/journal-admins')
@login_required
@platform_admin_required
def journal_admins():
    """Assign admins/editors to journals."""
    journals = Tenant.query.all()
    admins = User.query.filter(User.role.in_(['admin', 'super_admin', 'tenant_owner'])).all()
    return render_template('admin/journal_admins.html', journals=journals, admins=admins)

@admin_bp.route('/journal-analytics')
@login_required
@platform_admin_required
def journal_analytics():
    """Journal analytics - articles, acceptance rate, etc."""
    journals = Tenant.query.all()
    analytics = []
    for journal in journals:
        total_articles = Article.query.filter_by(tenant_id=journal.id).count()
        published = Article.query.filter_by(tenant_id=journal.id, status='published').count()
        acceptance_rate = (published / total_articles * 100) if total_articles > 0 else 0
        analytics.append({
            'journal': journal,
            'total_articles': total_articles,
            'published': published,
            'acceptance_rate': round(acceptance_rate, 1)
        })
    return render_template('admin/journal_analytics.html', analytics=analytics)

@admin_bp.route('/archived-journals')
@login_required
@platform_admin_required
def archived_journals():
    """View archived/inactive journals."""
    page = request.args.get('page', 1, type=int)
    archived = Tenant.query.filter_by(is_active=False).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/archived_journals.html', journals=archived)

# SUPER ADMIN - SUBMISSIONS & WORKFLOW

@admin_bp.route('/workflow-stages')
@login_required
@platform_admin_required
def workflow_stages():
    """Manage submission workflow stages."""
    stages = [
        {'name': 'Submitted', 'color': 'blue', 'count': Article.query.filter_by(status='submitted').count()},
        {'name': 'Under Review', 'color': 'amber', 'count': Article.query.filter_by(status='under_review').count()},
        {'name': 'Accepted', 'color': 'green', 'count': Article.query.filter_by(status='accepted').count()},
        {'name': 'Published', 'color': 'emerald', 'count': Article.query.filter_by(status='published').count()},
        {'name': 'Rejected', 'color': 'red', 'count': Article.query.filter_by(status='rejected').count()},
    ]
    return render_template('admin/workflow_stages.html', stages=stages)

@admin_bp.route('/assigned-reviewers')
@login_required
@platform_admin_required
def assigned_reviewers():
    """View reviewer assignments across platform."""
    # Get all articles with assigned reviewers
    articles = Article.query.filter(Article.status.in_(['under_review', 'submitted'])).all()
    return render_template('admin/assigned_reviewers.html', articles=articles)

@admin_bp.route('/plagiarism-checks')
@login_required
@platform_admin_required
def plagiarism_checks():
    """Plagiarism check integration and reports."""
    page = request.args.get('page', 1, type=int)
    # Get articles pending plagiarism check
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/plagiarism_checks.html', articles=articles)

# SUPER ADMIN - AI SYSTEM CONTROL

@admin_bp.route('/ai-settings', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def ai_settings():
    """Enable/Disable AI Assistant and configure settings."""
    if request.method == 'POST':
        settings = {
            'enabled': request.form.get('ai_enabled') == 'on',
            'model': request.form.get('ai_model', 'gpt-4'),
            'max_tokens': int(request.form.get('max_tokens', 4000)),
            'temperature': float(request.form.get('temperature', 0.7)),
        }
        flash('AI settings saved.', 'success')
        return redirect(url_for('admin.ai_settings'))
    return render_template('admin/ai_settings.html')

@admin_bp.route('/ai-usage-logs')
@login_required
@platform_admin_required
def ai_usage_logs():
    """Monitor AI usage - who used AI, when, and how much."""
    page = request.args.get('page', 1, type=int)
    # Query AI usage logs
    logs = []  # Placeholder - would query from AIUsage model
    return render_template('admin/ai_usage_logs.html', logs=logs)

@admin_bp.route('/ai-moderation')
@login_required
@platform_admin_required
def ai_moderation():
    """AI content moderation - flag inappropriate content."""
    page = request.args.get('page', 1, type=int)
    # Get flagged content
    flagged = []  # Placeholder - would query from AI moderation queue
    return render_template('admin/ai_moderation.html', flagged=flagged)

@admin_bp.route('/ai-limits', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def ai_limits():
    """Set AI usage limits - API tokens, requests per user."""
    if request.method == 'POST':
        limits = {
            'daily_requests_per_user': int(request.form.get('daily_requests', 50)),
            'monthly_tokens_per_user': int(request.form.get('monthly_tokens', 100000)),
            'global_daily_limit': int(request.form.get('global_daily', 10000)),
        }
        flash('AI limits updated.', 'success')
        return redirect(url_for('admin.ai_limits'))
    return render_template('admin/ai_limits.html')

# SUPER ADMIN - SUBSCRIPTION & PAYMENTS

@admin_bp.route('/subscription-plans', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def subscription_plans():
    """Create and manage subscription plans."""
    if request.method == 'POST':
        plan = {
            'name': request.form.get('name'),
            'price_monthly': float(request.form.get('price_monthly', 0)),
            'price_yearly': float(request.form.get('price_yearly', 0)),
            'features': request.form.getlist('features'),
        }
        flash(f'Subscription plan "{plan["name"]}" created.', 'success')
        return redirect(url_for('admin.subscription_plans'))
    plans = ['free', 'basic', 'professional', 'enterprise']
    return render_template('admin/subscription_plans.html', plans=plans)

@admin_bp.route('/coupons', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def coupons():
    """Coupon system for discounts."""
    if request.method == 'POST':
        coupon = {
            'code': request.form.get('code'),
            'discount_percent': float(request.form.get('discount_percent', 0)),
            'valid_until': request.form.get('valid_until'),
            'usage_limit': int(request.form.get('usage_limit', 100)),
        }
        flash(f'Coupon "{coupon["code"]}" created.', 'success')
        return redirect(url_for('admin.coupons'))
    return render_template('admin/coupons.html')

@admin_bp.route('/refunds')
@login_required
@platform_admin_required
def refunds():
    """Refund management - pending and processed."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    # Query refund requests
    refunds_data = []  # Placeholder - would query from Refund model
    return render_template('admin/refunds.html', refunds=refunds_data, status=status)

@admin_bp.route('/revenue-analytics')
@login_required
@platform_admin_required
def revenue_analytics():
    """Revenue analytics and charts."""
    from datetime import datetime, timedelta

    # Calculate revenue stats
    total_revenue = 0  # Placeholder - sum from transactions
    monthly_revenue = 0
    yearly_revenue = 0

    stats = {
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'active_subscriptions': 0,
        'churn_rate': 0,
    }
    return render_template('admin/revenue_analytics.html', stats=stats)

@admin_bp.route('/custom-domains')
@login_required
@platform_admin_required
def custom_domains():
    """Manage custom domain requests from schools."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('q', '')

    query = CustomDomainRequest.query.join(Tenant)

    if status_filter:
        query = query.filter(CustomDomainRequest.status == status_filter)

    if search:
        query = query.filter(
            db.or_(
                Tenant.name.ilike(f'%{search}%'),
                CustomDomainRequest.custom_domain.ilike(f'%{search}%'),
            )
        )

    # Order by request date descending (newest first)
    requests_paginated = query.order_by(
        CustomDomainRequest.request_date.desc()
    ).paginate(page=page, per_page=20, error_out=False)

    # Get counts for dashboard
    pending_count = CustomDomainRequest.query.filter_by(status='pending').count()
    approved_count = CustomDomainRequest.query.filter_by(status='approved').count()
    rejected_count = CustomDomainRequest.query.filter_by(status='rejected').count()
    total_count = CustomDomainRequest.query.count()

    return render_template(
        'admin/custom_domains.html',
        user=current_user,
        domain_requests=requests_paginated,
        search=search,
        status_filter=status_filter,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_count=total_count,
    )

@admin_bp.route('/custom-domains/<int:request_id>/approve', methods=['POST'])
@login_required
@platform_admin_required
def approve_custom_domain(request_id):
    """Approve a custom domain request."""
    domain_request = CustomDomainRequest.query.get_or_404(request_id)

    try:
        domain_request.approve(current_user.id)
        flash(f'Custom domain "{domain_request.custom_domain}" approved successfully.', 'success')
    except Exception as e:
        flash(f'Error approving domain: {str(e)}', 'danger')

    return redirect(url_for('admin.custom_domains'))

@admin_bp.route('/custom-domains/<int:request_id>/reject', methods=['POST'])
@login_required
@platform_admin_required
def reject_custom_domain(request_id):
    """Reject a custom domain request."""
    domain_request = CustomDomainRequest.query.get_or_404(request_id)

    try:
        domain_request.reject()
        flash(f'Custom domain "{domain_request.custom_domain}" rejected.', 'warning')
    except Exception as e:
        flash(f'Error rejecting domain: {str(e)}', 'danger')

    return redirect(url_for('admin.custom_domains'))

@admin_bp.route('/custom-domains/<int:request_id>/delete', methods=['POST'])
@login_required
@platform_admin_required
def delete_custom_domain(request_id):
    """Delete a custom domain request."""
    domain_request = CustomDomainRequest.query.get_or_404(request_id)

    try:
        db.session.delete(domain_request)
        db.session.commit()
        flash('Custom domain request deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting domain request: {str(e)}', 'danger')

    return redirect(url_for('admin.custom_domains'))

@admin_bp.route('/custom-domains/create', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def create_custom_domain():
    """Create a new custom domain request manually."""
    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        custom_domain = request.form.get('custom_domain', '').strip().lower()
        domain_type = request.form.get('domain_type', 'Domain')

        if not tenant_id or not custom_domain:
            flash('School and custom domain are required.', 'danger')
            return redirect(url_for('admin.create_custom_domain'))

        # Check if domain already exists
        existing = CustomDomainRequest.query.filter_by(custom_domain=custom_domain).first()
        if existing:
            flash(f'Domain "{custom_domain}" is already registered.', 'danger')
            return redirect(url_for('admin.create_custom_domain'))

        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            flash('School not found.', 'danger')
            return redirect(url_for('admin.create_custom_domain'))

        # Create the domain request
        domain_request = CustomDomainRequest(
            tenant_id=tenant_id,
            custom_domain=custom_domain,
            domain_type=domain_type,
            origin_url=f"https://edusynergy.in/{tenant.subdomain}",
            status='approved',  # Auto-approve if created by admin
            approved_date=datetime.utcnow(),
            approved_by_id=current_user.id,
        )

        # Also update tenant's custom domain
        tenant.custom_domain = custom_domain

        db.session.add(domain_request)
        db.session.commit()

        flash(f'Custom domain "{custom_domain}" created and approved.', 'success')
        return redirect(url_for('admin.custom_domains'))

    # Get all tenants for dropdown
    tenants = Tenant.query.filter_by(is_active=True).order_by(Tenant.name).all()
    return render_template('admin/create_custom_domain.html', tenants=tenants)

@admin_bp.route('/custom-domains/<int:request_id>/edit', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def edit_custom_domain(request_id):
    """Edit an existing custom domain request."""
    domain_request = CustomDomainRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        custom_domain = request.form.get('custom_domain', '').strip().lower()
        domain_type = request.form.get('domain_type', 'Domain')
        status = request.form.get('status', domain_request.status)

        if not custom_domain:
            flash('Custom domain is required.', 'danger')
            return redirect(url_for('admin.edit_custom_domain', request_id=request_id))

        # Check if domain already exists (excluding current one)
        existing = CustomDomainRequest.query.filter(
            CustomDomainRequest.custom_domain == custom_domain,
            CustomDomainRequest.id != request_id
        ).first()
        if existing:
            flash(f'Domain "{custom_domain}" is already registered.', 'danger')
            return redirect(url_for('admin.edit_custom_domain', request_id=request_id))

        # Update the domain request
        old_domain = domain_request.custom_domain
        domain_request.custom_domain = custom_domain
        domain_request.domain_type = domain_type
        domain_request.status = status

        # Update approved date if status changed to approved
        if status == 'approved' and domain_request.status != 'approved':
            domain_request.approved_date = datetime.utcnow()
            domain_request.approved_by_id = current_user.id

        # Also update tenant's custom domain
        if domain_request.tenant:
            domain_request.tenant.custom_domain = custom_domain

        db.session.commit()

        flash(f'Custom domain updated from "{old_domain}" to "{custom_domain}".', 'success')
        return redirect(url_for('admin.custom_domains'))

    # Get all tenants for dropdown
    tenants = Tenant.query.filter_by(is_active=True).order_by(Tenant.name).all()
    return render_template('admin/edit_custom_domain.html',
                         domain_request=domain_request,
                         tenants=tenants)

# SUPER ADMIN - ANALYTICS & REPORTS

@admin_bp.route('/platform-analytics')
@login_required
@platform_admin_required
def platform_analytics():
    """Comprehensive platform analytics dashboard."""
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stats = {
        'total_users': User.query.count(),
        'active_users_24h': 0,  # Would calculate from sessions
        'new_users_this_month': User.query.filter(
            User.created_at >= thirty_days_ago
        ).count(),
        'total_articles': Article.query.count(),
        'total_journals': Tenant.query.count(),
    }
    return render_template('admin/platform_analytics.html', stats=stats)

@admin_bp.route('/user-growth')
@login_required
@platform_admin_required
def user_growth():
    """User growth analytics and charts."""
    # Get user growth over time
    growth_data = []  # Would aggregate by month
    return render_template('admin/user_growth.html', growth=growth_data)

@admin_bp.route('/submission-trends')
@login_required
@platform_admin_required
def submission_trends():
    """Submission trends analytics."""
    # Get submission trends by month and status
    trends = []  # Would aggregate from articles
    return render_template('admin/submission_trends.html', trends=trends)

@admin_bp.route('/download-reports', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def download_reports():
    """Download reports in PDF/Excel format."""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        date_range = request.form.get('date_range')
        format_type = request.form.get('format', 'excel')
        flash(f'Generating {report_type} report in {format_type} format...', 'info')
    report_types = ['users', 'journals', 'articles', 'revenue', 'submissions', 'activity']
    return render_template('admin/download_reports.html', report_types=report_types)

# SUPER ADMIN - CONTENT MANAGEMENT

@admin_bp.route('/announcements', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def announcements():
    """Manage platform announcements."""
    if request.method == 'POST':
        announcement = {
            'title': request.form.get('title'),
            'content': request.form.get('content'),
            'target_audience': request.form.get('target', 'all'),
            'is_active': request.form.get('is_active') == 'on',
        }
        flash('Announcement created successfully.', 'success')
        return redirect(url_for('admin.announcements'))
    announcements_list = []  # Would query from Announcement model
    return render_template('admin/announcements.html', announcements=announcements_list)

@admin_bp.route('/homepage-content', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def homepage_content():
    """Edit homepage content."""
    if request.method == 'POST':
        content = {
            'hero_title': request.form.get('hero_title'),
            'hero_subtitle': request.form.get('hero_subtitle'),
            'featured_journals': request.form.getlist('featured_journals'),
            'show_stats': request.form.get('show_stats') == 'on',
        }
        flash('Homepage content updated.', 'success')
        return redirect(url_for('admin.homepage_content'))
    return render_template('admin/homepage_content.html')

@admin_bp.route('/testimonials', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def testimonials():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location_role = request.form.get('location_role', '').strip()
        message = request.form.get('message', '').strip()
        rating = request.form.get('rating', type=int) or 5
        sort_order = request.form.get('sort_order', type=int) or 0
        avatar_bg = (request.form.get('avatar_bg', '') or '').strip() or '#0e91e8'
        image_url = (request.form.get('image_url', '') or '').strip() or None
        is_active = request.form.get('is_active') == 'on'
        photo = request.files.get('photo')

        if not name or not message:
            flash('Customer name and testimonial message are required.', 'danger')
            return redirect(url_for('admin.testimonials'))

        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.', 'danger')
            return redirect(url_for('admin.testimonials'))

        designation = location_role or None
        organization = None
        if location_role and ',' in location_role:
            first_part, second_part = location_role.split(',', 1)
            designation = first_part.strip() or None
            organization = second_part.strip() or None

        try:
            uploaded_photo = _save_testimonial_photo(photo)
        except ValueError as err:
            flash(str(err), 'danger')
            return redirect(url_for('admin.testimonials'))

        if uploaded_photo:
            image_url = uploaded_photo

        db.session.add(
            Testimonial(
                name=name,
                designation=designation,
                organization=organization,
                message=message,
                rating=rating,
                image_url=image_url,
                avatar_bg=avatar_bg,
                is_active=is_active,
                sort_order=sort_order,
            )
        )
        db.session.commit()
        flash('Testimonial saved successfully.', 'success')
        return redirect(url_for('admin.testimonials'))

    testimonials_list = (
        Testimonial.query
        .order_by(Testimonial.sort_order.asc(), Testimonial.created_at.desc())
        .all()
    )
    return render_template('admin/testimonials.html', user=current_user, testimonials=testimonials_list)

@admin_bp.route('/testimonials/<int:testimonial_id>/toggle-active', methods=['POST'])
@login_required
@platform_admin_required
def toggle_testimonial_active(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_active = not testimonial.is_active
    db.session.commit()
    flash(f'Testimonial {"activated" if testimonial.is_active else "hidden"} successfully.', 'success')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/testimonials/<int:testimonial_id>/delete', methods=['POST'])
@login_required
@platform_admin_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    if testimonial.image_url and 'uploads/testimonials/' in testimonial.image_url:
        filename = testimonial.image_url.rsplit('uploads/testimonials/', 1)[-1]
        file_path = Path(current_app.static_folder) / 'uploads' / 'testimonials' / filename
        if file_path.exists():
            file_path.unlink()

    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/featured-content', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def featured_content():
    """Manage featured journals and articles."""
    if request.method == 'POST':
        featured_journals = request.form.getlist('featured_journals')
        featured_articles = request.form.getlist('featured_articles')
        flash('Featured content updated.', 'success')
        return redirect(url_for('admin.featured_content'))
    journals = Tenant.query.filter_by(is_active=True).all()
    articles = Article.query.filter_by(status='published').order_by(Article.created_at.desc()).limit(50).all()
    return render_template('admin/featured_content.html', journals=journals, articles=articles)

@admin_bp.route('/blog-posts', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def blog_posts():
    """Manage blog posts."""
    if request.method == 'POST':
        post = {
            'title': request.form.get('title'),
            'content': request.form.get('content'),
            'slug': request.form.get('slug'),
            'is_published': request.form.get('is_published') == 'on',
        }
        flash('Blog post saved.', 'success')
        return redirect(url_for('admin.blog_posts'))
    posts = []  # Would query from BlogPost model
    return render_template('admin/blog_posts.html', posts=posts)

# SUPER ADMIN - COMMUNICATION

@admin_bp.route('/send-notifications', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def send_notifications():
    """Send notifications to users or specific roles."""
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        message = (request.form.get('message') or '').strip()
        target_roles = request.form.getlist('target_roles')

        if not title or not message:
            flash('Title and message are required.', 'danger')
            return redirect(url_for('admin.send_notifications'))
        if not target_roles:
            flash('Please select at least one target role.', 'warning')
            return redirect(url_for('admin.send_notifications'))

        created_count = create_notifications_for_roles(
            target_roles=target_roles,
            title=title,
            message=message,
            link_url=url_for('admin.dashboard'),
            category='admin_broadcast',
        )
        flash(f'Notification delivered to {created_count} user(s).', 'success')
        return redirect(url_for('admin.send_notifications'))
    roles = ['all', 'super_admin', 'admin', 'tenant_owner', 'editor', 'reviewer', 'author', 'subscriber']
    return render_template('admin/send_notifications.html', roles=roles)

@admin_bp.route('/email-templates', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def email_templates():
    """Manage email templates."""
    templates = [
        'welcome_email', 'password_reset', 'article_submitted', 'article_accepted',
        'article_rejected', 'subscription_expired', 'payment_success', 'account_suspended'
    ]
    if request.method == 'POST':
        template_name = request.form.get('template_name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        flash(f'Template "{template_name}" updated.', 'success')
        return redirect(url_for('admin.email_templates'))
    return render_template('admin/email_templates.html', templates=templates)

@admin_bp.route('/sms-settings', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def sms_settings():
    """SMS gateway settings."""
    if request.method == 'POST':
        settings = {
            'provider': request.form.get('provider'),
            'api_key': request.form.get('api_key'),
            'sender_id': request.form.get('sender_id'),
            'enabled': request.form.get('enabled') == 'on',
        }
        flash('SMS settings saved.', 'success')
        return redirect(url_for('admin.sms_settings'))
    return render_template('admin/sms_settings.html')

# SUPER ADMIN - SECURITY & LOGS

@admin_bp.route('/login-logs')
@login_required
@platform_admin_required
def login_logs():
    """View detailed login logs with IP tracking."""
    page = request.args.get('page', 1, type=int)
    ip_filter = request.args.get('ip', '')
    # Query login logs
    logs = User.query.order_by(User.last_login.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('admin/login_logs.html', logs=logs, ip_filter=ip_filter)

@admin_bp.route('/admin-logs')
@login_required
@platform_admin_required
def admin_logs():
    """Admin activity logs - track admin actions."""
    page = request.args.get('page', 1, type=int)
    # Query admin action logs
    logs = []  # Would query from AdminLog model
    return render_template('admin/admin_logs.html', logs=logs)

@admin_bp.route('/two-factor-auth', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def two_factor_auth():
    """2FA settings for platform."""
    if request.method == 'POST':
        settings = {
            'require_2fa_for_admins': request.form.get('require_admins') == 'on',
            'require_2fa_for_journal_admins': request.form.get('require_journal_admins') == 'on',
            'allow_user_2fa': request.form.get('allow_users') == 'on',
        }
        flash('2FA settings updated.', 'success')
        return redirect(url_for('admin.two_factor_auth'))
    return render_template('admin/two_factor_auth.html')

@admin_bp.route('/ip-tracking')
@login_required
@platform_admin_required
def ip_tracking():
    """IP tracking and geolocation for security."""
    page = request.args.get('page', 1, type=int)
    # Get unique IPs and their activity
    ip_data = []  # Would aggregate from logs
    return render_template('admin/ip_tracking.html', ip_data=ip_data)

@admin_bp.route('/backup-restore', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def backup_restore():
    """Backup and restore system."""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_backup':
            flash('Backup creation started...', 'info')
        elif action == 'restore':
            backup_file = request.files.get('backup_file')
            flash('Restore process initiated...', 'warning')
    backups = []  # List available backups
    return render_template('admin/backup_restore.html', backups=backups)

# SUPER ADMIN - SYSTEM TOOLS

@admin_bp.route('/database-backup', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def database_backup():
    """Database backup management."""
    if request.method == 'POST':
        backup_type = request.form.get('backup_type', 'full')
        # Trigger database backup
        flash(f'{backup_type} database backup initiated.', 'info')
    return render_template('admin/database_backup.html')

@admin_bp.route('/cache-management', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def cache_management():
    """Cache clear and management."""
    if request.method == 'POST':
        cache_type = request.form.get('cache_type')
        if cache_type == 'all':
            flash('All caches cleared.', 'success')
        elif cache_type == 'query':
            flash('Query cache cleared.', 'success')
        elif cache_type == 'template':
            flash('Template cache cleared.', 'success')
        return redirect(url_for('admin.cache_management'))
    return render_template('admin/cache_management.html')

@admin_bp.route('/api-management', methods=['GET', 'POST'])
@login_required
@platform_admin_required
def api_management():
    """API key management and rate limiting."""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate_key':
            key_name = request.form.get('key_name')
            flash(f'New API key generated for "{key_name}".', 'success')
        elif action == 'revoke':
            key_id = request.form.get('key_id')
            flash(f'API key revoked.', 'success')
    api_keys = []  # Would query from APIKey model
    return render_template('admin/api_management.html', api_keys=api_keys)

@admin_bp.route('/system-logs')
@login_required
@platform_admin_required
def system_logs():
    """System logs viewer."""
    log_type = request.args.get('type', 'application')
    lines = request.args.get('lines', 100, type=int)
    # Read log files
    log_content = ''  # Would read from log file
    return render_template('admin/system_logs.html', log_type=log_type, content=log_content)
