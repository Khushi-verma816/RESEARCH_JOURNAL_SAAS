"""
Phase 5: Complete Blog System
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
    'app/routes/blog.py': '''"""
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
''',

    'app/templates/blog/index.html': '''{% extends "base.html" %}

{% block title %}Blog - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
        <h1 style="color: #007bff; margin: 0;">📝 Research Blog</h1>
        {% if current_user.is_authenticated %}
        <a href="{{ url_for('blog.create') }}" 
           style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 6px;">
            ✍️ Write Post
        </a>
        {% endif %}
    </div>
    
    <p style="color: #666; margin-bottom: 30px;">
        Insights, research updates, and knowledge sharing from our community.
    </p>
    
    {% if posts %}
        <div style="display: grid; gap: 30px;">
            {% for post in posts %}
            <article style="border-bottom: 1px solid #e9ecef; padding-bottom: 30px;">
                <h2 style="margin: 0 0 10px 0;">
                    <a href="{{ url_for('blog.view', post_id=post.id) }}" 
                       style="color: #007bff; text-decoration: none;">
                        {{ post.title }}
                    </a>
                </h2>
                
                <div style="display: flex; gap: 15px; margin-bottom: 15px; color: #666; font-size: 14px;">
                    <span>👤 {{ post.author.full_name }}</span>
                    <span>📅 {{ post.published_at.strftime('%B %d, %Y') if post.published_at else post.created_at.strftime('%B %d, %Y') }}</span>
                    <span>👁️ {{ post.views_count }} views</span>
                </div>
                
                <p style="color: #666; line-height: 1.6; margin-bottom: 15px;">
                    {{ post.excerpt }}
                </p>
                
                <a href="{{ url_for('blog.view', post_id=post.id) }}" 
                   style="color: #007bff; text-decoration: none; font-weight: bold;">
                    Read more →
                </a>
            </article>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 60px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="color: #666; margin-bottom: 15px;">No blog posts yet</h3>
            <p style="color: #999; margin-bottom: 25px;">Be the first to share your insights!</p>
            {% if current_user.is_authenticated %}
            <a href="{{ url_for('blog.create') }}" 
               style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">
                Write Your First Post
            </a>
            {% endif %}
        </div>
    {% endif %}
</div>
{% endblock %}
''',

    'app/templates/blog/view.html': '''{% extends "base.html" %}

{% block title %}{{ post.title }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="max-width: 800px; margin: 0 auto;">
    <article style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <!-- Header -->
        <header style="margin-bottom: 30px;">
            <h1 style="color: #333; margin-bottom: 20px; font-size: 36px; line-height: 1.2;">
                {{ post.title }}
            </h1>
            
            <div style="display: flex; gap: 20px; align-items: center; padding: 15px 0; border-top: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 40px; height: 40px; background: #007bff; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        {{ post.author.first_name[0] }}{{ post.author.last_name[0] }}
                    </div>
                    <div>
                        <div style="font-weight: bold; color: #333;">{{ post.author.full_name }}</div>
                        <div style="font-size: 14px; color: #666;">
                            {{ post.published_at.strftime('%B %d, %Y') if post.published_at else post.created_at.strftime('%B %d, %Y') }}
                        </div>
                    </div>
                </div>
                <div style="margin-left: auto; color: #666; font-size: 14px;">
                    👁️ {{ post.views_count }} views
                </div>
            </div>
            
            {% if post.status == 'draft' %}
            <div style="background: #fff3cd; padding: 10px 15px; border-radius: 4px; margin-top: 15px;">
                <strong>⚠️ Draft:</strong> This post is not published yet.
            </div>
            {% endif %}
        </header>
        
        <!-- Content -->
        <div style="color: #333; line-height: 1.8; font-size: 18px;">
            {{ post.content|replace('\n', '<br>')|safe }}
        </div>
        
        <!-- Footer Actions -->
        <footer style="margin-top: 40px; padding-top: 30px; border-top: 1px solid #e9ecef;">
            {% if current_user.is_authenticated and current_user.id == post.author_id %}
            <div style="display: flex; gap: 10px;">
                <a href="{{ url_for('blog.edit', post_id=post.id) }}" 
                   style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    ✏️ Edit
                </a>
                <form method="POST" action="{{ url_for('blog.delete', post_id=post.id) }}" 
                      onsubmit="return confirm('Are you sure you want to delete this post?');"
                      style="display: inline;">
                    <button type="submit" 
                            style="padding: 10px 20px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🗑️ Delete
                    </button>
                </form>
            </div>
            {% endif %}
            
            <div style="margin-top: 20px;">
                <a href="{{ url_for('blog.index') }}" 
                   style="color: #007bff; text-decoration: none;">
                    ← Back to Blog
                </a>
            </div>
        </footer>
    </article>
</div>
{% endblock %}
''',

    'app/templates/blog/create.html': '''{% extends "base.html" %}

{% block title %}Create Blog Post - Research Journal SaaS{% endblock %}

{% block content %}
<div style="max-width: 900px; margin: 0 auto;">
    <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #007bff; margin-bottom: 30px;">✍️ Write Blog Post</h1>
        
        <form method="POST">
            <!-- Title -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Title <span style="color: red;">*</span>
                </label>
                <input type="text" name="title" required
                       placeholder="Enter an engaging title..."
                       style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 18px; transition: border-color 0.3s;"
                       onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'">
            </div>
            
            <!-- Excerpt -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Excerpt <span style="color: #999; font-weight: normal; font-size: 14px;">(optional - auto-generated if empty)</span>
                </label>
                <textarea name="excerpt" rows="3"
                          placeholder="Brief summary of your post (shown in listings)..."
                          style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; resize: vertical; transition: border-color 0.3s;"
                          onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'"></textarea>
            </div>
            
            <!-- Content -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Content <span style="color: red;">*</span>
                </label>
                <textarea name="content" rows="20" required
                          placeholder="Write your content here... (Markdown supported in future versions)"
                          style="width: 100%; padding: 15px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; line-height: 1.6; resize: vertical; font-family: 'Georgia', serif; transition: border-color 0.3s;"
                          onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'"></textarea>
            </div>
            
            <!-- Buttons -->
            <div style="display: flex; gap: 10px; justify-content: space-between;">
                <div style="display: flex; gap: 10px;">
                    <button type="submit" name="action" value="draft"
                            style="padding: 12px 24px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background 0.3s;"
                            onmouseover="this.style.background='#5a6268'" onmouseout="this.style.background='#6c757d'">
                        💾 Save as Draft
                    </button>
                    <button type="submit" name="action" value="publish"
                            style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background 0.3s;"
                            onmouseover="this.style.background='#218838'" onmouseout="this.style.background='#28a745'">
                        🚀 Publish Now
                    </button>
                </div>
                <a href="{{ url_for('blog.my_posts') }}" 
                   style="padding: 12px 24px; background: #e9ecef; color: #333; text-decoration: none; border-radius: 6px; font-size: 16px; display: inline-block;">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''',

    'app/templates/blog/edit.html': '''{% extends "base.html" %}

{% block title %}Edit {{ post.title }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="max-width: 900px; margin: 0 auto;">
    <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #007bff; margin-bottom: 30px;">✏️ Edit Blog Post</h1>
        
        <form method="POST">
            <!-- Title -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Title <span style="color: red;">*</span>
                </label>
                <input type="text" name="title" value="{{ post.title }}" required
                       style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 18px; transition: border-color 0.3s;"
                       onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'">
            </div>
            
            <!-- Excerpt -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Excerpt
                </label>
                <textarea name="excerpt" rows="3"
                          style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; resize: vertical; transition: border-color 0.3s;"
                          onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'">{{ post.excerpt }}</textarea>
            </div>
            
            <!-- Content -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold; font-size: 16px;">
                    Content <span style="color: red;">*</span>
                </label>
                <textarea name="content" rows="20" required
                          style="width: 100%; padding: 15px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; line-height: 1.6; resize: vertical; font-family: 'Georgia', serif; transition: border-color 0.3s;"
                          onfocus="this.style.borderColor='#007bff'" onblur="this.style.borderColor='#ddd'">{{ post.content }}</textarea>
            </div>
            
            <!-- Status Info -->
            <div style="padding: 15px; background: {% if post.status == 'published' %}#d4edda{% else %}#fff3cd{% endif %}; border-radius: 6px; margin-bottom: 25px;">
                <strong>Current Status:</strong> 
                <span style="text-transform: uppercase;">{{ post.status }}</span>
                {% if post.published_at %}
                    (Published on {{ post.published_at.strftime('%B %d, %Y') }})
                {% endif %}
            </div>
            
            <!-- Buttons -->
            <div style="display: flex; gap: 10px; justify-content: space-between;">
                <div style="display: flex; gap: 10px;">
                    <button type="submit" name="action" value="save"
                            style="padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                        💾 Save Changes
                    </button>
                    {% if post.status == 'draft' %}
                    <button type="submit" name="action" value="publish"
                            style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                        🚀 Publish Now
                    </button>
                    {% else %}
                    <button type="submit" name="action" value="unpublish"
                            style="padding: 12px 24px; background: #ffc107; color: #333; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                        📥 Unpublish
                    </button>
                    {% endif %}
                </div>
                <a href="{{ url_for('blog.my_posts') }}" 
                   style="padding: 12px 24px; background: #e9ecef; color: #333; text-decoration: none; border-radius: 6px; font-size: 16px; display: inline-block;">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''',

    'app/templates/blog/my_posts.html': '''{% extends "base.html" %}

{% block title %}My Blog Posts - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
        <h1 style="color: #007bff; margin: 0;">📝 My Blog Posts</h1>
        <a href="{{ url_for('blog.create') }}" 
           style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 6px;">
            ✍️ New Post
        </a>
    </div>
    
    {% if posts %}
        <div style="display: grid; gap: 20px;">
            {% for post in posts %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">
                            <a href="{{ url_for('blog.view', post_id=post.id) }}" 
                               style="color: #007bff; text-decoration: none;">
                                {{ post.title }}
                            </a>
                        </h3>
                        
                        <p style="color: #666; margin: 10px 0; line-height: 1.6;">
                            {{ post.excerpt }}
                        </p>
                        
                        <div style="display: flex; gap: 15px; margin-top: 10px; font-size: 14px; color: #666;">
                            <span>
                                {% if post.status == 'published' %}
                                    <span style="background: #28a745; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">
                                        ✅ PUBLISHED
                                    </span>
                                {% else %}
                                    <span style="background: #ffc107; color: #333; padding: 4px 10px; border-radius: 12px; font-size: 11px;">
                                        📝 DRAFT
                                    </span>
                                {% endif %}
                            </span>
                            <span>📅 {{ post.created_at.strftime('%B %d, %Y') }}</span>
                            <span>👁️ {{ post.views_count }} views</span>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-left: 20px;">
                        <a href="{{ url_for('blog.edit', post_id=post.id) }}" 
                           style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">
                            Edit
                        </a>
                        <form method="POST" action="{{ url_for('blog.delete', post_id=post.id) }}" 
                              onsubmit="return confirm('Are you sure you want to delete this post?');"
                              style="display: inline;">
                            <button type="submit" 
                                    style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                                Delete
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 60px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="color: #666; margin-bottom: 15px;">No blog posts yet</h3>
            <p style="color: #999; margin-bottom: 25px;">Start sharing your research insights with the community!</p>
            <a href="{{ url_for('blog.create') }}" 
               style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">
                Write Your First Post
            </a>
        </div>
    {% endif %}
</div>
{% endblock %}
''',
}

print("Creating Phase 5 files...\n")
for filepath, content in files.items():
    create_file(filepath, content)

print("\n" + "="*60)
print("✅ PHASE 5 FILES CREATED SUCCESSFULLY!")
print("="*60)
print("\nNext steps:")
print("1. Update app/__init__.py to register blog blueprint")
print("2. Update homepage Quick Actions for blog link")
print("3. Restart Flask")
print("4. Test the blog system!")