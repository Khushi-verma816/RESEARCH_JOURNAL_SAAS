from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models.article import Article
from app.models.tenant import Tenant
from app.models.user import User
from app.models.testimonial import Testimonial
from app.modules.main import main_bp
from datetime import datetime, timedelta

DEFAULT_TESTIMONIALS = [
    {
        'name': 'Dr. Rajesh Mehta',
        'designation': 'Editor-in-Chief',
        'organization': 'IIT Delhi Journal',
        'message': 'Research Hub completely transformed how we manage our journal. The AI assistant alone saves our editors 10+ hours per week.',
        'rating': 5,
        'avatar_bg': '#0e91e8',
        'image_url': '/static/uploads/testimonials/rajesh_mehta.png',
        'sort_order': 1,
    },
    {
        'name': 'Prof. Sarah Chen',
        'designation': 'Director',
        'organization': 'Oxford Open Science',
        'message': 'Setting up our custom journal took less than a day. The peer review workflow is seamless and our authors love the experience.',
        'rating': 5,
        'avatar_bg': '#7c3aed',
        'image_url': '/static/uploads/testimonials/sarah_chen.png',
        'sort_order': 2,
    },
    {
        'name': 'Dr. Amit Kumar',
        'designation': 'Managing Editor',
        'organization': 'AIIMS Research',
        'message': 'The analytics dashboard gives us insights we never had before. We can finally see which articles are making the biggest impact.',
        'rating': 5,
        'avatar_bg': '#059669',
        'image_url': '/static/uploads/testimonials/amit_kumar.png',
        'sort_order': 3,
    },
]

def _ensure_testimonials():
    db.create_all()

    active_count = Testimonial.query.filter_by(is_active=True).count()
    if active_count > 0:
        return

    for item in DEFAULT_TESTIMONIALS:
        db.session.add(Testimonial(**item))

    db.session.commit()

@main_bp.route('/')
def index():
    _ensure_testimonials()
    testimonials = (
        Testimonial.query
        .filter_by(is_active=True)
        .order_by(Testimonial.sort_order.asc(), Testimonial.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template('main/index.html', testimonials=testimonials)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    # Non-admin dashboard must always be personal-only (no other users' data).
    scoped_articles = Article.query.filter_by(author_id=current_user.id)

    stats = {
        'total': scoped_articles.count(),
        'published': scoped_articles.filter_by(status='published').count(),
        'under_review': scoped_articles.filter(Article.status.in_(['submitted', 'under_review'])).count(),
        'views': int(
            scoped_articles.with_entities(
                db.func.coalesce(db.func.sum(Article.views), 0)
            ).scalar() or 0
        ),
    }
    recent_articles = scoped_articles.order_by(Article.created_at.desc()).limit(8).all()
    my_tenant = Tenant.query.get(current_user.tenant_id) if current_user.tenant_id else None

    # ── Analytics data (scoped to tenant if tenant_owner, else author-only) ──────
    # Resolve tenant_id: tenant_owners own a journal via Tenant.owner_id
    # but their user.tenant_id may be null
    effective_tenant_id = current_user.tenant_id
    if not effective_tenant_id and current_user.is_tenant_owner():
        owned_tenant = Tenant.query.filter_by(owner_id=current_user.id).first()
        if owned_tenant:
            effective_tenant_id = owned_tenant.id

    if effective_tenant_id:
        all_a = Article.query.filter_by(tenant_id=effective_tenant_id).all()
    else:
        all_a = Article.query.filter_by(author_id=current_user.id).all()

    published_arts    = [a for a in all_a if a.status == 'published']
    under_review_arts = [a for a in all_a if a.status == 'under_review']
    submitted_arts    = [a for a in all_a if a.status == 'submitted']
    rejected_arts     = [a for a in all_a if a.status == 'rejected']
    draft_arts        = [a for a in all_a if a.status == 'draft']

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
        count = len([a for a in all_a if month_start <= a.created_at < month_end])
        monthly_data.append({'month': month_start.strftime('%b %Y'), 'count': count})

    categories = {}
    for a in all_a:
        cat = getattr(a, 'category', None) or 'Uncategorized'
        categories[cat] = categories.get(cat, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:6]

    if effective_tenant_id:
        members   = User.query.filter_by(tenant_id=effective_tenant_id).all()
        authors   = [m for m in members if m.role == 'author']
        reviewers = [m for m in members if m.role == 'reviewer']
        editors   = [m for m in members if m.role in ['editor', 'tenant_owner']]
    else:
        authors = reviewers = editors = []

    return render_template(
        'admin/dashboard.html',
        user=current_user,
        my_tenant=my_tenant,
        dashboard_mode='member',
        stats=stats,
        recent_articles=recent_articles,
        # Analytics data
        status_data=status_data,
        monthly_data=monthly_data,
        top_articles=top_articles,
        top_categories=top_categories,
        authors=authors,
        reviewers=reviewers,
        editors=editors,
    )
