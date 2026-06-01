"""Compatibility wrapper for legacy imports.

Use `app.core.extensions` as the single source of truth.
"""

from app.core.extensions import db, login_manager, mail, migrate

# Configure Flask-Login defaults on the shared login manager instance.
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
