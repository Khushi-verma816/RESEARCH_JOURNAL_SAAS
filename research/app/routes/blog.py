"""
Blog routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.blog import BlogPost, BlogCategory
from app.utils.decorators import tenant_required, role_required
from datetime import datetime

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
@tenant_required
def index():
    """Blog homepage"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = BlogPost.query.filter_by(
        tenant_id=request.tenant.id,
        status='published'
    )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    posts = query.order_by(BlogPost.published_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    categories = BlogCategory.query.filter_by(
        tenant_id=request.tenant.id,
        is_active=True
    ).all()
    
    return render_template('blog/index.html', 
                         posts=posts, 
                         categories=categories)


@blog_bp.route('/post/<slug>')
@tenant_required
def view_post(slug):
    """View blog post"""
    post = BlogPost.query.filter_by(
        tenant_id=request.tenant.id,
        slug=slug,
        status='published'
    ).first_or_404()
    
    # Increment views
    post.views_count += 1
    db.session.commit()
    
    return render_template('blog/view_post.html', post=post)


@blog_bp.route('/create', methods=['GET', 'POST'])
@login_required
@tenant_required
@role_required('admin', 'editor', 'author')
def create_post():
    """Create blog post"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category_id = request.form.get('category_id', type=int)
        tags = request.form.get('tags', '').strip().split(',')
        tags = [t.strip() for t in tags if t.strip()]
        status = request.form.get('status', 'draft')
        
        post = BlogPost(
            tenant_id=request.tenant.id,
            author_id=current_user.id,
            category_id=category_id,
            title=title,
            content=content,
            excerpt=excerpt,
            tags=tags,
            status=status
        )
        post.generate_slug()
        
        if status == 'published':
            post.published_at = datetime.utcnow()
        
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('blog.my_posts'))
    
    categories = BlogCategory.query.filter_by(
        tenant_id=request.tenant.id,
        is_active=True
    ).all()
    
    return render_template('blog/create_post.html', categories=categories)


@blog_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_post(post_id):
    """Edit blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    # Check access
    if post.author_id != current_user.id and \
       not current_user.has_role('admin') and \
       not current_user.has_role('editor'):
        flash('Access denied', 'danger')
        return redirect(url_for('blog.my_posts'))
    
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.excerpt = request.form.get('excerpt', '').strip()
        post.category_id = request.form.get('category_id', type=int)
        
        tags = request.form.get('tags', '').strip().split(',')
        post.tags = [t.strip() for t in tags if t.strip()]
        
        old_status = post.status
        post.status = request.form.get('status', 'draft')
        
        # If publishing for first time
        if old_status == 'draft' and post.status == 'published':
            post.published_at = datetime.utcnow()
        
        post.generate_slug()
        db.session.commit()
        
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('blog.my_posts'))
    
    categories = BlogCategory.query.filter_by(
        tenant_id=request.tenant.id,
        is_active=True
    ).all()
    
    return render_template('blog/edit_post.html', 
                         post=post, 
                         categories=categories)


@blog_bp.route('/my-posts')
@login_required
@tenant_required
def my_posts():
    """View user's blog posts"""
    page = request.args.get('page', 1, type=int)
    
    posts = BlogPost.query.filter_by(author_id=current_user.id)\
        .order_by(BlogPost.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('blog/my_posts.html', posts=posts)


@blog_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
@tenant_required
def delete_post(post_id):
    """Delete blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    # Check access
    if post.author_id != current_user.id and not current_user.has_role('admin'):
        flash('Access denied', 'danger')
        return redirect(url_for('blog.my_posts'))
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('blog.my_posts'))


@blog_bp.route('/categories')
@login_required
@tenant_required
@role_required('admin', 'editor')
def categories():
    """Manage blog categories"""
    categories = BlogCategory.query.filter_by(tenant_id=request.tenant.id)\
        .order_by(BlogCategory.name).all()
    
    return render_template('blog/categories.html', categories=categories)


@blog_bp.route('/category/create', methods=['POST'])
@login_required
@tenant_required
@role_required('admin', 'editor')
def create_category():
    """Create blog category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    category = BlogCategory(
        tenant_id=request.tenant.id,
        name=name,
        slug=slugify(name),
        description=description,
        is_active=True
    )
    
    db.session.add(category)
    db.session.commit()
    
    flash('Category created successfully!', 'success')
    return redirect(url_for('blog.categories'))