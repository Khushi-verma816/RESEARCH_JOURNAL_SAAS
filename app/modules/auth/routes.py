from urllib.parse import urljoin, urlparse
import re

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.modules.auth import auth_bp
from app.modules.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription
from app.core.notifications import notify_platform_admins
from app.core.extensions import db
from app.core.email import send_email
from datetime import datetime

def _is_safe_next_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def _is_allowed_next_for_user(user, target):
    if not target:
        return False
    normalized = target.lower()
    if normalized.startswith('/admin') and not user.is_admin():
        return False
    return True

def _default_landing_for(user):
    if user.is_admin():
        return url_for('admin.dashboard')
    return url_for('main.dashboard')

def _normalize_subdomain_seed(value):
    seed = re.sub(r'[^a-z0-9]+', '-', (value or '').lower()).strip('-')
    return seed[:40] if seed else ''

def _build_unique_subdomain(seed):
    candidate = seed
    suffix = 2
    while Tenant.query.filter_by(subdomain=candidate).first():
        candidate = f'{seed}-{suffix}'
        suffix += 1
    return candidate

def _ensure_non_admin_owner_setup(user):
    # Request requirement: every non-admin account should behave like payment owner account.
    if user.is_admin():
        return

    if user.role != 'tenant_owner':
        user.role = 'tenant_owner'

    tenant = Tenant.query.filter_by(owner_id=user.id).first()
    if not tenant:
        local_part = (user.email or '').split('@')[0]
        seed = _normalize_subdomain_seed(f'{user.first_name}-{user.last_name}') or _normalize_subdomain_seed(local_part)
        if not seed:
            seed = f'user-{user.id}'
        subdomain = _build_unique_subdomain(seed)

        tenant = Tenant(
            name=f"{user.full_name}'s Journal",
            subdomain=subdomain,
            description='Auto-created journal for account setup.',
            owner_id=user.id,
            is_active=True,
            is_verified=True,
            plan='free',
            contact_email=user.email,
        )
        db.session.add(tenant)
        db.session.flush()
    else:
        tenant.owner_id = user.id
        tenant.is_active = True

    user.tenant_id = tenant.id

    sub = Subscription.query.filter_by(tenant_id=tenant.id).first()
    if not sub:
        db.session.add(
            Subscription(
                tenant_id=tenant.id,
                plan='free',
                status='active',
                amount=0.0,
                billing_cycle='monthly',
            )
        )

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(_default_landing_for(current_user))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.lower().strip(),
            role='subscriber'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        _ensure_non_admin_owner_setup(user)
        db.session.commit()
        notify_platform_admins(
            title='New user registered',
            message=f'{user.full_name} ({user.email}) created a new account.',
            link_url=url_for('admin.users'),
            exclude_user_ids=[user.id],
        )
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_default_landing_for(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Account deactivated. Contact support.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            _ensure_non_admin_owner_setup(user)
            db.session.commit()
            flash(f'Welcome back, {user.first_name}!', 'success')
            next_page = request.args.get('next')
            if _is_safe_next_url(next_page) and _is_allowed_next_for_user(user, next_page):
                return redirect(next_page)
            return redirect(_default_landing_for(user))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(_default_landing_for(current_user))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()

            # Send reset email
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # Create professional HTML email
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; }}
  .card {{ background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #0ea5e9, #6366f1); padding: 32px; text-align: center; }}
  .header-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
  .header-title {{ color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }}
  .header-sub {{ color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 6px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 1rem; color: #1e293b; margin-bottom: 16px; font-weight: 600; }}
  .message {{ font-size: 0.9rem; color: #475569; line-height: 1.7; margin-bottom: 24px; }}
  .info-box {{ background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 20px; margin-bottom: 24px; }}
  .info-text {{ font-size: 0.85rem; color: #0369a1; margin: 0; }}
  .btn-wrap {{ text-align: center; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 32px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; }}
  .divider {{ border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }}
  .footer {{ text-align: center; padding: 20px 32px; background: #f8fafc; }}
  .footer-text {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.8; }}
  .security-note {{ background: #fef9c3; border: 1px solid #fde047; border-radius: 8px; padding: 16px; margin-bottom: 24px; }}
  .security-text {{ font-size: 0.83rem; color: #713f12; margin: 0; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="header-icon">🔐</div>
      <div class="header-title">Password Reset Request</div>
      <div class="header-sub">Research Hub · Academic Publishing Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello {user.first_name},</div>
      <div class="message">
        We received a request to reset your password for your Research Hub account.
        Click the button below to create a new password.
      </div>
      <div class="btn-wrap">
        <a href="{reset_url}" class="btn">🔑 Reset My Password</a>
      </div>
      <div class="info-box">
        <p class="info-text">
          <strong>⏰ This link expires in 1 hour</strong><br>
          For security reasons, this password reset link will expire after 1 hour.
        </p>
      </div>
      <hr class="divider">
      <div class="security-note">
        <p class="security-text">
          <strong>⚠️ Didn't request this?</strong><br>
          If you didn't request a password reset, please ignore this email.
          Your password will remain unchanged and your account is secure.
        </p>
      </div>
      <div class="message" style="font-size:0.83rem;margin-bottom:0;color:#94a3b8">
        If the button doesn't work, copy and paste this link into your browser:<br>
        <a href="{reset_url}" style="color:#0ea5e9;word-break:break-all">{reset_url}</a>
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">
        © 2026 Research Hub · Academic Publishing Platform<br>
        This is an automated email, please do not reply.
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

            try:
                send_email(
                    to=user.email,
                    subject='🔐 Password Reset Request - Research Hub',
                    body_html=html_body
                )
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                flash('Unable to send email. Please try again later.', 'danger')
                print(f"Email error: {e}")
        else:
            # Don't reveal if email exists or not (security best practice)
            flash('If that email is registered, you will receive password reset instructions.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(_default_landing_for(current_user))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()

        flash('Your password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)
