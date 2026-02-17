"""
Search & Filter routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Journal, Submission, BlogPost, User
from app.extensions import db

search_bp = Blueprint('search', __name__)

@search_bp.route('/')
@login_required
def index():
    """Main search page"""
    query = request.args.get('q', '').strip()
    filter_type = request.args.get('type', 'all')
    status_filter = request.args.get('status', 'all')
    
    results = {
        'journals': [],
        'submissions': [],
        'blogs': [],
        'total': 0
    }
    
    if query:
        # Search Journals
        if filter_type in ['all', 'journals']:
            journals = Journal.query.filter(
                db.or_(
                    Journal.name.ilike(f'%{query}%'),
                    Journal.description.ilike(f'%{query}%')
                ),
                Journal.is_active == True
            ).all()
            results['journals'] = journals
        
        # Search Submissions
        if filter_type in ['all', 'submissions']:
            sub_query = Submission.query.filter(
                db.or_(
                    Submission.title.ilike(f'%{query}%'),
                    Submission.abstract.ilike(f'%{query}%')
                )
            )
            
            # Apply status filter
            if status_filter != 'all':
                sub_query = sub_query.filter(
                    Submission.status == status_filter
                )
            
            # Non-admins only see their own
            if not (current_user.has_role('admin') or 
                    current_user.has_role('editor')):
                sub_query = sub_query.filter(
                    Submission.user_id == current_user.id
                )
            
            results['submissions'] = sub_query.all()
        
        # Search Blog Posts
        if filter_type in ['all', 'blogs']:
            blogs = BlogPost.query.filter(
                db.or_(
                    BlogPost.title.ilike(f'%{query}%'),
                    BlogPost.content.ilike(f'%{query}%')
                ),
                BlogPost.is_published == True
            ).all()
            results['blogs'] = blogs
        
        results['total'] = (
            len(results['journals']) + 
            len(results['submissions']) + 
            len(results['blogs'])
        )
    
    return render_template('search/index.html',
                         query=query,
                         results=results,
                         filter_type=filter_type,
                         status_filter=status_filter)

@search_bp.route('/api')
@login_required
def api_search():
    """API endpoint for live search"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    results = []
    
    # Search journals
    journals = Journal.query.filter(
        Journal.name.ilike(f'%{query}%'),
        Journal.is_active == True
    ).limit(3).all()
    
    for j in journals:
        results.append({
            'type': 'journal',
            'icon': '📋',
            'title': j.name,
            'subtitle': 'Journal',
            'url': f'/journal/{j.id}'
        })
    
    # Search submissions
    sub_query = Submission.query.filter(
        Submission.title.ilike(f'%{query}%')
    )
    if not (current_user.has_role('admin') or 
            current_user.has_role('editor')):
        sub_query = sub_query.filter(
            Submission.user_id == current_user.id
        )
    submissions = sub_query.limit(3).all()
    
    for s in submissions:
        results.append({
            'type': 'submission',
            'icon': '📄',
            'title': s.title,
            'subtitle': f'Submission • {s.status.title()}',
            'url': f'/journal/submission/{s.id}'
        })
    
    # Search blogs
    blogs = BlogPost.query.filter(
        BlogPost.title.ilike(f'%{query}%'),
        BlogPost.is_published == True
    ).limit(3).all()
    
    for b in blogs:
        results.append({
            'type': 'blog',
            'icon': '📝',
            'title': b.title,
            'subtitle': 'Blog Post',
            'url': f'/blog/{b.id}'
        })
    
    return jsonify({'results': results[:8]})

@search_bp.route('/journals')
@login_required
def filter_journals():
    """Filter journals page"""
    name_filter = request.args.get('name', '').strip()
    status_filter = request.args.get('status', 'all')
    
    query = Journal.query
    
    if name_filter:
        query = query.filter(
            Journal.name.ilike(f'%{name_filter}%')
        )
    
    if status_filter == 'accepting':
        query = query.filter(
            Journal.is_accepting_submissions == True
        )
    elif status_filter == 'closed':
        query = query.filter(
            Journal.is_accepting_submissions == False
        )
    
    journals = query.filter_by(is_active=True).all()
    
    return render_template('search/journals.html',
                         journals=journals,
                         name_filter=name_filter,
                         status_filter=status_filter)

@search_bp.route('/submissions')
@login_required
def filter_submissions():
    """Filter submissions page"""
    title_filter = request.args.get('title', '').strip()
    status_filter = request.args.get('status', 'all')
    journal_filter = request.args.get('journal', 'all')
    
    query = Submission.query
    
    # Non-admins only see their own
    if not (current_user.has_role('admin') or 
            current_user.has_role('editor')):
        query = query.filter_by(user_id=current_user.id)
    
    if title_filter:
        query = query.filter(
            Submission.title.ilike(f'%{title_filter}%')
        )
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if journal_filter != 'all':
        query = query.filter_by(journal_id=journal_filter)
    
    submissions = query.order_by(
        Submission.submitted_at.desc()
    ).all()
    
    # Get all journals for filter dropdown
    from app.models import Journal
    journals = Journal.query.filter_by(is_active=True).all()
    
    return render_template('search/submissions.html',
                         submissions=submissions,
                         title_filter=title_filter,
                         status_filter=status_filter,
                         journal_filter=journal_filter,
                         journals=journals)