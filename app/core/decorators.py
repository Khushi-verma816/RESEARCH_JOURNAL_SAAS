from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def tenant_owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.can_manage_tenant():
            flash('Journal Owner access required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated

def editor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_editor():
            flash('Editor access required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated
