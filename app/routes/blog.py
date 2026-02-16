"""
Blog routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import BlogPost
from datetime import datetime

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    """View all published blog posts"""
    posts = BlogPost.query.filter_by(status='published').order_by(
        BlogPost.published_at.desc()
    ).all()
    
    return render_template('blog/index.html', posts=posts)

@blog_bp.route('/<int:post_id>')
def view(post_id):
    """View a single blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    # Only show published posts to non-authors
    if post.status != 'published' and post.author_id != current_user.id:
        flash('This blog post is not published yet', 'warning')
        return redirect(url_for('blog.index'))
    
    # Increment views
    post.views_count += 1
    db.session.commit()
    
    return render_template('blog/view.html', post=post)

@blog_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        action = request.form.get('action')
        
        if not title or not content:
            flash('Title and content are required', 'danger')
            return render_template('blog/create.html')
        
        # Auto-generate excerpt if not provided
        if not excerpt:
            excerpt = content[:200] + '...' if len(content) > 200 else content
        
        post = BlogPost(
            tenant_id=current_user.tenant_id,
            author_id=current_user.id,
            title=title,
            content=content,
            excerpt=excerpt,
            status='draft'
        )
        
        # If publish button was clicked
        if action == 'publish':
            post.status = 'published'
            post.published_at = datetime.utcnow()
        
        db.session.add(post)
        db.session.commit()
        
        if post.status == 'published':
            flash('Blog post published successfully!', 'success')
        else:
            flash('Blog post saved as draft', 'success')
        
        return redirect(url_for('blog.my_posts'))
    
    return render_template('blog/create.html')

@blog_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """Edit a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    # Check if user is the author
    if post.author_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('blog.index'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        action = request.form.get('action')
        
        if not title or not content:
            flash('Title and content are required', 'danger')
            return render_template('blog/edit.html', post=post)
        
        post.title = title
        post.content = content
        post.excerpt = excerpt or (content[:200] + '...' if len(content) > 200 else content)
        
        # Handle publish/unpublish
        if action == 'publish' and post.status == 'draft':
            post.status = 'published'
            post.published_at = datetime.utcnow()
        elif action == 'unpublish':
            post.status = 'draft'
        
        db.session.commit()
        
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('blog.my_posts'))
    
    return render_template('blog/edit.html', post=post)

@blog_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    """Delete a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    # Check if user is the author
    if post.author_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('blog.index'))
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post deleted successfully', 'success')
    return redirect(url_for('blog.my_posts'))

@blog_bp.route('/my-posts')
@login_required
def my_posts():
    """View user's blog posts"""
    posts = BlogPost.query.filter_by(author_id=current_user.id).order_by(
        BlogPost.created_at.desc()
    ).all()
    
    return render_template('blog/my_posts.html', posts=posts)
