from functools import wraps
from flask import request, abort
from flask_login import current_user


def tenant_required(f):
    """Ensure request has tenant context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, "tenant"):
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Ensure user has required role"""
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            if not any(current_user.has_role(role) for role in roles):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return wrapper
