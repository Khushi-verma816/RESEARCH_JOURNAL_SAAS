"""
Tenant management routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User, Role
from app.models.subscription import Subscription, SubscriptionPlan
from app.utils.decorators import role_required, tenant_required
from app.utils.validators import validate_subdomain
from slugify import slugify

tenant_bp = Blueprint('tenant', __name__)


@tenant_bp.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    """Tenant onboarding process"""
    if request.method == 'POST':
        step = request.form.get('step', '1')
        
        if step == '1':
            # Step 1: Basic Information
            org_name = request.form.get('org_name', '').strip()
            subdomain = request.form.get('subdomain', '').strip().lower()
            email = request.form.get('email', '').strip().lower()
            
            # Validate subdomain
            is_valid, error_msg = validate_subdomain(subdomain)
            if not is_valid:
                flash(error_msg, 'danger')
                return render_template('tenant/onboarding.html', step=1)
            
            # Check if subdomain is available
            if Tenant.query.filter_by(subdomain=subdomain).first():
                flash('Subdomain is already taken', 'danger')
                return render_template('tenant/onboarding.html', step=1)
            
            # Store in session for next step
            request.session['onboarding_data'] = {
                'org_name': org_name,
                'subdomain': subdomain,
                'email': email
            }
            
            return render_template('tenant/onboarding.html', step=2)
        
        elif step == '2':
            # Step 2: Admin Account
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            password = request.form.get('password', '')
            
            onboarding_data = request.session.get('onboarding_data', {})
            
            # Create tenant
            tenant = Tenant(
                name=onboarding_data['org_name'],
                subdomain=onboarding_data['subdomain'],
                email=onboarding_data['email'],
                is_active=True,
                is_verified=False
            )
            db.session.add(tenant)
            db.session.flush()
            
            # Create admin user
            admin_user = User(
                tenant_id=tenant.id,
                email=onboarding_data['email'],
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_email_verified=True
            )
            admin_user.set_password(password)
            
            # Assign admin role
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Administrator')
                db.session.add(admin_role)
                db.session.flush()
            
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            
            # Create trial subscription
            trial_plan = SubscriptionPlan.query.filter_by(slug='trial').first()
            if trial_plan:
                subscription = Subscription(
                    tenant_id=tenant.id,
                    plan_id=trial_plan.id
                )
                subscription.start_trial(days=14)
                db.session.add(subscription)
            
            db.session.commit()
            
            # Clear session
            request.session.pop('onboarding_data', None)
            
            flash('Tenant created successfully! You can now log in.', 'success')
            
            # Redirect to tenant subdomain
            tenant_url = f"http://{tenant.subdomain}.localhost:5000/auth/login"
            return redirect(tenant_url)
    
    return render_template('tenant/onboarding.html', step=1)


@tenant_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@tenant_required
@role_required('admin')
def settings():
    """Tenant settings"""
    tenant = request.tenant
    
    if request.method == 'POST':
        # Update tenant information
        tenant.name = request.form.get('name', tenant.name)
        tenant.email = request.form.get('email', tenant.email)
        tenant.phone = request.form.get('phone', tenant.phone)
        tenant.address_line1 = request.form.get('address_line1', tenant.address_line1)
        tenant.address_line2 = request.form.get('address_line2', tenant.address_line2)
        tenant.city = request.form.get('city', tenant.city)
        tenant.state = request.form.get('state', tenant.state)
        tenant.country = request.form.get('country', tenant.country)
        tenant.postal_code = request.form.get('postal_code', tenant.postal_code)
        tenant.theme_color = request.form.get('theme_color', tenant.theme_color)
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('tenant.settings'))
    
    return render_template('tenant/settings.html', tenant=tenant)


@tenant_bp.route('/users', methods=['GET'])
@login_required
@tenant_required
@role_required('admin')
def users():
    """List all users in tenant"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.filter_by(tenant_id=request.tenant.id)\
        .order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('tenant/users.html', users=users)


@tenant_bp.route('/users/invite', methods=['GET', 'POST'])
@login_required
@tenant_required
@role_required('admin')
def invite_user():
    """Invite new user"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role_id = request.form.get('role_id', type=int)
        
        # Check if user already exists
        if User.query.filter_by(tenant_id=request.tenant.id, email=email).first():
            flash('User with this email already exists', 'danger')
            return redirect(url_for('tenant.users'))
        
        # Check tenant user limit
        if not request.tenant.can_add_user():
            flash('User limit reached. Please upgrade your plan.', 'warning')
            return redirect(url_for('tenant.users'))
        
        # Create user
        user = User(
            tenant_id=request.tenant.id,
            email=email,
            is_active=True,
            is_email_verified=False
        )
        
        # Generate temporary password
        temp_password = generate_token(12)
        user.set_password(temp_password)
        
        # Assign role
        if role_id:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        db.session.add(user)
        db.session.commit()
        
        # Send invitation email (TODO)
        flash(f'User invited successfully! Temporary password: {temp_password}', 'success')
        return redirect(url_for('tenant.users'))
    
    roles = Role.query.all()
    return render_template('tenant/invite_user.html', roles=roles)


@tenant_bp.route('/custom-domain', methods=['GET', 'POST'])
@login_required
@tenant_required
@role_required('admin')
def custom_domain():
    """Configure custom domain"""
    tenant = request.tenant
    
    if request.method == 'POST':
        domain = request.form.get('domain', '').strip().lower()
        
        # Validate domain format
        if not domain or '.' not in domain:
            flash('Invalid domain format', 'danger')
            return redirect(url_for('tenant.custom_domain'))
        
        # Check if domain is already in use
        if Tenant.query.filter_by(custom_domain=domain).filter(Tenant.id != tenant.id).first():
            flash('Domain is already in use', 'danger')
            return redirect(url_for('tenant.custom_domain'))
        
        tenant.custom_domain = domain
        db.session.commit()
        
        flash('Custom domain updated! Please configure your DNS settings.', 'success')
        return redirect(url_for('tenant.custom_domain'))
    
    return render_template('tenant/custom_domain.html', tenant=tenant)


@tenant_bp.route('/api/check-subdomain', methods=['POST'])
def check_subdomain():
    """API endpoint to check subdomain availability"""
    subdomain = request.json.get('subdomain', '').strip().lower()
    
    # Validate format
    is_valid, error_msg = validate_subdomain(subdomain)
    if not is_valid:
        return jsonify({'available': False, 'message': error_msg})
    
    # Check availability
    exists = Tenant.query.filter_by(subdomain=subdomain).first()
    
    return jsonify({
        'available': not exists,
        'message': 'Subdomain is available' if not exists else 'Subdomain is already taken'
    })