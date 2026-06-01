# app/modules/articles/routes.py

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.modules.articles import articles_bp
from app.modules.articles.forms import SubmitArticleForm, ReviewArticleForm, EditorDecisionForm
from app.models.article import Article
from app.models.tenant import Tenant
from app.models.user import User
from app.core.notifications import create_notifications_for_users, notify_platform_admins
from app.core.extensions import db
from datetime import datetime

def _resolve_editor_tenant_id():
    """Return the effective tenant_id for the current user's editorial scope.
    For tenant_owners who own a journal via owner_id but may not have
    tenant_id set on their user record.
    """
    if current_user.tenant_id:
        return current_user.tenant_id
    if current_user.is_tenant_owner():
        owned = Tenant.query.filter_by(owner_id=current_user.id).first()
        if owned:
            return owned.id
    return None

# MY ARTICLES (author view)

@articles_bp.route('/my-articles')
@login_required
def my_articles():
    articles = Article.query.filter_by(
        author_id=current_user.id
    ).order_by(Article.created_at.desc()).all()

    return render_template(
        'articles/my_articles.html',
        articles=articles,
        user=current_user
    )

# SUBMIT ARTICLE

@articles_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    # User must belong to a tenant
    if not current_user.tenant_id:
        if current_user.can_manage_tenant():
            flash('Create your journal first before submitting an article.', 'warning')
            return redirect(url_for('tenants.create_journal'))

        flash('You are not linked to any journal yet. Ask your journal admin to add you before submitting.', 'warning')
        return redirect(url_for('articles.my_articles'))

    form = SubmitArticleForm()

    if form.validate_on_submit():
        article = Article(
            tenant_id  = current_user.tenant_id,
            author_id  = current_user.id,
            title      = form.title.data.strip(),
            abstract   = form.abstract.data.strip(),
            keywords   = form.keywords.data,
            category   = form.category.data,
            co_authors = form.co_authors.data,
            content    = form.content.data,
        )

        # Check which button was clicked
        if form.save_draft.data:
            article.status = 'draft'
            db.session.add(article)
            db.session.commit()
            flash('Article saved as draft.', 'info')
        else:
            article.status       = 'submitted'
            article.submitted_at = datetime.utcnow()
            db.session.add(article)
            db.session.commit()
            notify_platform_admins(
                title='Article submitted',
                message=f'"{article.title}" submitted by {current_user.full_name}.',
                link_url=url_for('admin.submissions'),
                exclude_user_ids=[current_user.id],
            )
            flash('Article submitted successfully! The editor will review it shortly.', 'success')

        return redirect(url_for('articles.my_articles'))

    return render_template('articles/submit.html', form=form, user=current_user)

# VIEW ARTICLE (public)

@articles_bp.route('/article/<int:article_id>')
def view(article_id):
    article = Article.query.get_or_404(article_id)

    # Only published articles are publicly visible
    # Authors, editors, reviewers can see their own
    if article.status != 'published':
        if not current_user.is_authenticated:
            abort(404)
        if (current_user.id != article.author_id and
                not current_user.is_editor() and
                current_user.id != article.reviewer_id):
            abort(404)

    article.increment_views()

    return render_template('articles/view.html', article=article, user=current_user)

# EDIT ARTICLE (author, draft/submitted only)

@articles_bp.route('/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(article_id):
    article = Article.query.get_or_404(article_id)

    # Only author can edit, and only if draft or submitted
    if article.author_id != current_user.id:
        flash('You can only edit your own articles.', 'danger')
        return redirect(url_for('articles.my_articles'))

    if article.status not in ['draft', 'submitted']:
        flash('You cannot edit an article that is under review or published.', 'warning')
        return redirect(url_for('articles.my_articles'))

    form = SubmitArticleForm(obj=article)

    if form.validate_on_submit():
        article.title      = form.title.data.strip()
        article.abstract   = form.abstract.data.strip()
        article.keywords   = form.keywords.data
        article.category   = form.category.data
        article.co_authors = form.co_authors.data
        article.content    = form.content.data
        article.updated_at = datetime.utcnow()

        if form.save_draft.data:
            article.status = 'draft'
            flash('Draft saved.', 'info')
        else:
            article.status       = 'submitted'
            article.submitted_at = datetime.utcnow()
            flash('Article resubmitted successfully!', 'success')

        db.session.commit()
        if not form.save_draft.data:
            notify_platform_admins(
                title='Article resubmitted',
                message=f'"{article.title}" was resubmitted by {current_user.full_name}.',
                link_url=url_for('admin.submissions'),
                exclude_user_ids=[current_user.id],
            )
        return redirect(url_for('articles.my_articles'))

    return render_template('articles/submit.html', form=form, article=article, user=current_user)

# DELETE ARTICLE (draft only)

@articles_bp.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete(article_id):
    article = Article.query.get_or_404(article_id)

    if article.author_id != current_user.id:
        flash('You can only delete your own articles.', 'danger')
        return redirect(url_for('articles.my_articles'))

    if article.status != 'draft':
        flash('You can only delete draft articles.', 'warning')
        return redirect(url_for('articles.my_articles'))

    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'info')
    return redirect(url_for('articles.my_articles'))

# EDITOR PANEL — all articles (editors) or assigned (reviewers)

@articles_bp.route('/editor/panel')
@login_required
def editor_panel():
    is_editor  = current_user.is_editor()
    is_reviewer = current_user.is_reviewer()

    if not is_editor and not is_reviewer:
        flash('Editor or Reviewer access required.', 'danger')
        abort(403)

    if is_editor:
        # Resolve tenant_id properly for tenant_owners (who may own a tenant
        # via Tenant.owner_id but have a null tenant_id on their user record)
        effective_tenant_id = _resolve_editor_tenant_id()
        if effective_tenant_id:
            articles = Article.query.filter_by(
                tenant_id=effective_tenant_id
            ).order_by(Article.created_at.desc()).all()
        else:
            # Platform admin — show all articles
            articles = Article.query.order_by(Article.created_at.desc()).all()
    else:
        # Reviewers only see articles assigned to them
        articles = Article.query.filter_by(
            reviewer_id=current_user.id
        ).order_by(Article.created_at.desc()).all()

    submitted    = [a for a in articles if a.status == 'submitted']
    under_review = [a for a in articles if a.status == 'under_review']
    accepted     = [a for a in articles if a.status == 'accepted']
    published    = [a for a in articles if a.status == 'published']
    rejected     = [a for a in articles if a.status == 'rejected']
    drafts       = [a for a in articles if a.status == 'draft']

    return render_template(
        'articles/editor_panel.html',
        user         = current_user,
        all_articles = articles,
        submitted    = submitted,
        under_review = under_review,
        accepted     = accepted,
        published    = published,
        rejected     = rejected,
        drafts       = drafts,
        is_editor    = is_editor,
    )

# EDITOR — assign reviewer

@articles_bp.route('/editor/article/<int:article_id>/assign', methods=['POST'])
@login_required
def assign_reviewer(article_id):
    if not current_user.is_editor():
        abort(403)

    article     = Article.query.get_or_404(article_id)
    reviewer_id = request.form.get('reviewer_id')

    if not reviewer_id:
        flash('Please select a reviewer.', 'warning')
        return redirect(url_for('articles.editor_panel'))

    reviewer = User.query.get(reviewer_id)
    if not reviewer:
        flash('Invalid reviewer.', 'danger')
        return redirect(url_for('articles.editor_panel'))

    # Verify reviewer belongs to same tenant as article
    if reviewer.tenant_id != article.tenant_id:
        flash('Reviewer must belong to the same journal.', 'danger')
        return redirect(url_for('articles.editor_panel'))

    article.reviewer_id = reviewer.id
    article.status      = 'under_review'
    article.editor_id   = current_user.id
    db.session.commit()

    create_notifications_for_users(
        user_ids=[reviewer.id],
        title='New review assignment',
        message=f'You were assigned to review "{article.title}".',
        link_url=url_for('articles.review_article', article_id=article.id),
        category='review_assignment',
    )

    flash(f'Article assigned to {reviewer.full_name} for review.', 'success')
    return redirect(url_for('articles.editor_panel'))

# EDITOR — final decision (publish/reject)

@articles_bp.route('/editor/article/<int:article_id>/decision', methods=['GET', 'POST'])
@login_required
def editor_decision(article_id):
    if not current_user.is_editor():
        abort(403)

    article = Article.query.get_or_404(article_id)
    form    = EditorDecisionForm()

    if form.validate_on_submit():
        article.editor_id    = current_user.id
        article.editor_notes = form.editor_notes.data
        notification_title = None
        notification_message = None
        notification_link = url_for('articles.my_articles')

        if form.decision.data == 'publish':
            article.status       = 'published'
            article.published_at = datetime.utcnow()
            article.generate_doi()
            notification_title = 'Article published'
            notification_message = f'Your article "{article.title}" is now published.'
            notification_link = url_for('articles.view', article_id=article.id)
            flash(f'Article published! DOI: {article.doi}', 'success')
        elif form.decision.data == 'accept':
            article.status = 'accepted'
            notification_title = 'Article accepted'
            notification_message = f'Your article "{article.title}" has been accepted.'
            flash('Article accepted.', 'success')
        elif form.decision.data == 'reject':
            article.status = 'rejected'
            notification_title = 'Article rejected'
            notification_message = f'Your article "{article.title}" was rejected.'
            flash('Article rejected.', 'info')

        db.session.commit()
        if notification_title and notification_message:
            create_notifications_for_users(
                user_ids=[article.author_id],
                title=notification_title,
                message=notification_message,
                link_url=notification_link,
                category='article_status',
            )
        return redirect(url_for('articles.editor_panel'))

    return render_template(
        'articles/editor_decision.html',
        article=article, form=form, user=current_user
    )

# REVIEWER — submit review

@articles_bp.route('/review/article/<int:article_id>', methods=['GET', 'POST'])
@login_required
def review_article(article_id):
    article = Article.query.get_or_404(article_id)

    # Only assigned reviewer or editor can review
    if (article.reviewer_id != current_user.id and
            not current_user.is_editor()):
        flash('You are not assigned to review this article.', 'danger')
        abort(403)

    form = ReviewArticleForm()

    if form.validate_on_submit():
        article.review_notes = form.review_notes.data

        if form.decision.data == 'accept':
            article.status = 'accepted'
        elif form.decision.data in ['minor_revision', 'major_revision']:
            article.status = 'submitted'  # Sends back for revision
        elif form.decision.data == 'reject':
            article.status = 'rejected'

        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('articles.editor_panel'))

    return render_template(
        'articles/review.html',
        article=article, form=form, user=current_user
    )

# JOURNAL PUBLIC PAGE — published articles

@articles_bp.route('/journal/<subdomain>/articles')
def journal_articles(subdomain):
    tenant = Tenant.query.filter_by(
        subdomain=subdomain, is_active=True
    ).first_or_404()

    articles = Article.query.filter_by(
        tenant_id=tenant.id,
        status='published'
    ).order_by(Article.published_at.desc()).all()

    return render_template(
        'articles/journal_articles.html',
        tenant=tenant,
        articles=articles
    )
