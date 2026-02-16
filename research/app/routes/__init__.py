"""
Routes package initialization
"""
from app.routes.auth import auth_bp
from app.routes.tenant import tenant_bp
from app.routes.journal import journal_bp
from app.routes.blog import blog_bp
from app.routes.subscription import subscription_bp
from app.routes.ai import ai_bp
from app.routes.video import video_bp

__all__ = [
    'auth_bp',
    'tenant_bp',
    'journal_bp',
    'blog_bp',
    'subscription_bp',
    'ai_bp',
    'video_bp'
]