# app/modules/search/routes.py

from flask import render_template, request
from flask_login import login_required
from app.modules.search import search_bp
from app.models.article import Article
from app.models.tenant import Tenant
from app.models.user import User
from app.core.extensions import db

@search_bp.route('/search')
@login_required
def search():
    query       = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    page        = request.args.get('page', 1, type=int)

    articles = []
    journals = []
    authors  = []
    total    = 0

    if query:
        if search_type in ('all', 'articles'):
            articles = Article.query.filter(
                Article.status == 'published',
                db.or_(
                    Article.title.ilike(f'%{query}%'),
                    Article.abstract.ilike(f'%{query}%'),
                    Article.keywords.ilike(f'%{query}%'),
                    Article.category.ilike(f'%{query}%'),
                )
            ).order_by(Article.published_at.desc()).all()

        if search_type in ('all', 'journals'):
            journals = Tenant.query.filter(
                Tenant.is_active == True,
                db.or_(
                    Tenant.name.ilike(f'%{query}%'),
                    Tenant.description.ilike(f'%{query}%'),
                )
            ).all()

        if search_type in ('all', 'authors'):
            authors = User.query.filter(
                db.or_(
                    User.first_name.ilike(f'%{query}%'),
                    User.last_name.ilike(f'%{query}%'),
                )
            ).all()

        total = len(articles) + len(journals) + len(authors)

    return render_template(
        'search/results.html',
        query=query,
        search_type=search_type,
        articles=articles,
        journals=journals,
        authors=authors,
        total=total,
    )
