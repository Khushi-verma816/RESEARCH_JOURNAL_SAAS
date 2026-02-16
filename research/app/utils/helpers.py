"""
Helper utility functions
"""
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import current_app, url_for
import bleach


def generate_token(length=32):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_file(file, folder='uploads'):
    """Save uploaded file and return the path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Add timestamp to prevent overwrites
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return filepath
    
    return None


def sanitize_html(html_content):
    """Sanitize HTML content to prevent XSS"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'img']
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title']
    }
    
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)


def format_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime object"""
    if dt is None:
        return ''
    return dt.strftime(format)


def time_ago(dt):
    """Get human-readable time difference"""
    if dt is None:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return format_datetime(dt, '%B %d, %Y')


def paginate_query(query, page, per_page=20):
    """Paginate a SQLAlchemy query"""
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num
    }


def generate_verification_url(token, endpoint='auth.verify_email'):
    """Generate email verification URL"""
    return url_for(endpoint, token=token, _external=True)


def generate_password_reset_url(token):
    """Generate password reset URL"""
    return url_for('auth.reset_password', token=token, _external=True)