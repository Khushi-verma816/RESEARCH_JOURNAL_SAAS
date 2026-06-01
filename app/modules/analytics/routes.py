# app/modules/analytics/routes.py

from flask import render_template, abort
from flask_login import login_required, current_user
from app.modules.analytics import analytics_bp
from app.models.article import Article
from app.models.user import User
from app.models.tenant import Tenant
from app.core.extensions import db
from datetime import datetime, timedelta

def _resolve_analytics_tenant_id():
    """Resolve tenant_id for analytics scope.
    Tenant owners who created a journal via owner_id may have null tenant_id.
    """
    if current_user.tenant_id:
        return current_user.tenant_id
    if current_user.is_tenant_owner():
        owned = Tenant.query.filter_by(owner_id=current_user.id).first()
        if owned:
            return owned.id
    return None

@analytics_bp.route('/analytics')
@login_required
def dashboard():
    # Allow editors, tenant_owners, admins, and super_admins
    if not (current_user.is_editor() or current_user.is_admin()):
        abort(403)

    tenant_id = _resolve_analytics_tenant_id()

    # ── Article stats ──────────────────────────
    if tenant_id:
        all_articles = Article.query.filter_by(tenant_id=tenant_id).all()
    elif current_user.is_admin():
        # Super/platform admin: show platform-wide article stats
        all_articles = Article.query.all()
    else:
        all_articles = []

    total_articles   = len(all_articles)
    published        = [a for a in all_articles if a.status == 'published']
    under_review     = [a for a in all_articles if a.status == 'under_review']
    submitted        = [a for a in all_articles if a.status == 'submitted']
    rejected         = [a for a in all_articles if a.status == 'rejected']
    drafts           = [a for a in all_articles if a.status == 'draft']

    total_views      = sum(a.views for a in all_articles)
    published_views  = sum(a.views for a in published)

    # ── Top articles by views ──────────────────
    top_articles = sorted(published, key=lambda a: a.views, reverse=True)[:5]

    # ── Recent activity (last 30 days) ─────────
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_articles = [a for a in all_articles if a.created_at >= thirty_days_ago]

    # ── Member stats ───────────────────────────
    if tenant_id:
        members       = User.query.filter_by(tenant_id=tenant_id).all()
        total_members = len(members)
        authors       = [m for m in members if m.role == 'author']
        reviewers     = [m for m in members if m.role == 'reviewer']
        editors       = [m for m in members if m.role in ['editor', 'tenant_owner']]
    else:
        total_members = 0
        authors = reviewers = editors = []

    # ── Status breakdown for chart ─────────────
    status_data = {
        'Published':    len(published),
        'Under Review': len(under_review),
        'Submitted':    len(submitted),
        'Rejected':     len(rejected),
        'Draft':        len(drafts),
    }

    # ── Monthly submissions (last 6 months) ────
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end   = month_start + timedelta(days=31)
        count = len([a for a in all_articles
                     if month_start <= a.created_at < month_end])
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })

    # ── Category breakdown ─────────────────────
    categories = {}
    for a in all_articles:
        cat = a.category or 'Uncategorized'
        categories[cat] = categories.get(cat, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:6]

    return render_template(
        'analytics/dashboard.html',
        user            = current_user,
        total_articles  = total_articles,
        total_published = len(published),
        total_views     = total_views,
        published_views = published_views,
        total_members   = total_members,
        under_review    = len(under_review),
        submitted_count = len(submitted),
        top_articles    = top_articles,
        recent_articles = recent_articles,
        status_data     = status_data,
        monthly_data    = monthly_data,
        top_categories  = top_categories,
        authors         = authors,
        reviewers       = reviewers,
        editors         = editors,
    )