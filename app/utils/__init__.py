# app/utils/__init__.py
# DEPRECATED: All email functions have been consolidated into app/core/email.py
# This re-exports from utils/email.py for backward compatibility.

from app.utils.email import (
    send_email,
    send_renewal_reminder,
    send_plan_expired,
    send_upgrade_confirmation,
    send_subscription_cancelled,
    send_trial_expiry_warning,
    send_subscription_renewal,
    send_subscription_expired,
    send_expiring_soon,
    send_welcome_email,
)