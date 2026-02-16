"""
Authentication routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User, Role
from app.models.tenant import Tenant
from app.utils.decorators import tenant_required
from app.utils.validators import validate_email, validate_password
from app.utils.helpers import generate_token
from app.services.smtp_service import SMTPService
from datetime import datetime, timedelta
import pyotp

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@tenant_required
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validation
        errors = []
        
        # Validate email
        is_valid_email, email_msg = validate_email(email)
        if not is_valid_email:
            errors.append(email_msg)
        else:
            email = email_msg
        
        # Check if email already exists in this tenant
        if User.query.filter_by(tenant_id=request.tenant.id, email=email).first():
            errors.append("Email already registered")
        
        # Validate password
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        is_valid_password, password_errors = validate_password(password)
        if not is_valid_password:
            errors.extend(password_errors)
        
        if not first_name or not last_name:
            errors.append("First name and last name are required")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            tenant_id=request.tenant.id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_email_verified=False
        )
        user.set_password(password)
        
        # Generate email verification token
        token = user.generate_email_verification_token()
        
        # Assign default role
        default_role = Role.query.filter_by(name='user').first()
        if default_role:
            user.roles.append(default_role)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        SMTPService.send_verification_email(email, verification_url, first_name)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@tenant_required
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(
            tenant_id=request.tenant.id,
            email=email
        ).first()
        
        if not user:
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.is_locked():
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'danger')
            return render_template('auth/login.html')
        
        # Verify password
        if not user.check_password(password):
            user.increment_login_attempts()
            db.session.commit()
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('auth/login.html')
        
        # Reset login attempts
        user.reset_login_attempts()
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Check if 2FA is enabled
        if user.two_factor_enabled:
            # Store user_id in session for 2FA verification
            request.session['pending_2fa_user_id'] = user.id
            return redirect(url_for('auth.verify_2fa'))
        
        # Login user
        login_user(user, remember=remember)
        
        flash('Login successful!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('auth.login'))
    
    user.is_email_verified = True
    user.email_verification_token = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@tenant_required
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        user = User.query.filter_by(
            tenant_id=request.tenant.id,
            email=email
        ).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            db.session.commit()
            
            # Send reset email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            SMTPService.send_password_reset_email(email, reset_url, user.first_name)
        
        # Always show success message (security best practice)
        flash('If an account exists with this email, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password"""
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.password_reset_expires or \
       user.password_reset_expires < datetime.utcnow():
        flash('Invalid or expired reset link', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Validate password
        is_valid, errors = validate_password(password)
        if not is_valid:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Set up two-factor authentication"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'enable':
            # Generate secret
            secret = pyotp.random_base32()
            current_user.two_factor_secret = secret
            db.session.commit()
            
            # Generate QR code URI
            totp = pyotp.TOTP(secret)
            qr_uri = totp.provisioning_uri(
                current_user.email,
                issuer_name=request.tenant.name
            )
            
            return render_template('auth/setup_2fa.html', 
                                 qr_uri=qr_uri, 
                                 secret=secret,
                                 setup_complete=False)
        
        elif action == 'verify':
            code = request.form.get('code', '')
            totp = pyotp.TOTP(current_user.two_factor_secret)
            
            if totp.verify(code):
                current_user.two_factor_enabled = True
                db.session.commit()
                flash('Two-factor authentication enabled successfully!', 'success')
                return redirect(url_for('dashboard.settings'))
            else:
                flash('Invalid verification code', 'danger')
                return render_template('auth/setup_2fa.html', 
                                     qr_uri=None,
                                     setup_complete=False)
        
        elif action == 'disable':
            current_user.two_factor_enabled = False
            current_user.two_factor_secret = None
            db.session.commit()
            flash('Two-factor authentication disabled', 'info')
            return redirect(url_for('dashboard.settings'))
    
    return render_template('auth/setup_2fa.html', setup_complete=True)


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA code during login"""
    user_id = request.session.get('pending_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        code = request.form.get('code', '')
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if totp.verify(code):
            # Remove pending session
            request.session.pop('pending_2fa_user_id', None)
            
            # Login user
            login_user(user, remember=request.form.get('remember', False))
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid verification code', 'danger')
    
    return render_template('auth/verify_2fa.html')