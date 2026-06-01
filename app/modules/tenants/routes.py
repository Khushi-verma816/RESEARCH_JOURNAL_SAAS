# app/modules/tenants/routes.py

from flask import render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from app.modules.tenants import tenants_bp
from app.modules.tenants.forms import CreateTenantForm, UpdateTenantForm
from app.models.tenant import Tenant
from app.models.user import User
from app.core.notifications import notify_platform_admins
from app.core.extensions import db
from app.core.decorators import tenant_owner_required
from datetime import datetime

def _managed_tenant_for_current_user():
    tenant = Tenant.query.filter_by(owner_id=current_user.id).first()
    if tenant:
        return tenant
    if current_user.tenant_id:
        return Tenant.query.get(current_user.tenant_id)
    return None

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CREATE JOURNAL (Tenant)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@tenants_bp.route('/create-journal', methods=['GET', 'POST'])
@login_required
def create_journal():
    """Any logged-in user can create their own journal"""

    # If user already owns a tenant, redirect to it
    existing = Tenant.query.filter_by(owner_id=current_user.id).first()
    if existing:
        flash('You already have a journal. Manage it from your dashboard.', 'info')
        return redirect(url_for('tenants.manage_journal'))

    form = CreateTenantForm()

    if form.validate_on_submit():
        tenant = Tenant(
            name          = form.name.data.strip(),
            subdomain     = form.subdomain.data.lower().strip(),
            description   = form.description.data,
            contact_email = form.contact_email.data,
            owner_id      = current_user.id,
            is_active     = True
        )
        db.session.add(tenant)
        db.session.flush()  # Get tenant.id before commit

        # Associate user to tenant. Keep platform admin roles unchanged.
        current_user.tenant_id = tenant.id
        if current_user.role not in ['super_admin', 'admin']:
            current_user.role = 'tenant_owner'

        db.session.commit()
        notify_platform_admins(
            title='New journal created',
            message=f'{current_user.full_name} created "{tenant.name}" journal.',
            link_url=url_for('admin.journals'),
            exclude_user_ids=[current_user.id],
        )

        flash(f'ðŸŽ‰ Journal "{tenant.name}" created successfully!', 'success')
        return redirect(url_for('tenants.manage_journal'))

    return render_template('tenants/create_journal.html', form=form)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MANAGE JOURNAL (Tenant Dashboard)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@tenants_bp.route('/manage-journal', methods=['GET', 'POST'])
@login_required
@tenant_owner_required
def manage_journal():
    """Tenant owner manages their journal settings"""

    tenant = _managed_tenant_for_current_user()

    if not tenant:
        flash('You do not have a journal yet.', 'warning')
        return redirect(url_for('tenants.create_journal'))

    form = UpdateTenantForm(obj=tenant)

    if form.validate_on_submit():
        tenant.name           = form.name.data.strip()
        tenant.description    = form.description.data
        tenant.contact_email  = form.contact_email.data
        tenant.website_url    = form.website_url.data
        tenant.primary_color  = form.primary_color.data or '#0272c6'
        tenant.secondary_color= form.secondary_color.data or '#38adf8'
        tenant.footer_text    = form.footer_text.data
        tenant.updated_at     = datetime.utcnow()

        db.session.commit()
        flash('Journal settings updated successfully!', 'success')
        return redirect(url_for('tenants.manage_journal'))

    # Get journal members
    members = User.query.filter_by(tenant_id=tenant.id).all()

    return render_template(
        'tenants/manage_journal.html',
        tenant  = tenant,
        form    = form,
        members = members
    )

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# INVITE MEMBER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@tenants_bp.route('/invite-member', methods=['POST'])
@login_required
@tenant_owner_required
def invite_member():
    """Invite a user to join as a team member"""

    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    email  = request.form.get('email', '').strip().lower()
    role   = request.form.get('role', 'author')

    if not email:
        flash('Please enter an email address.', 'danger')
        return redirect(url_for('tenants.manage_journal'))

    # Check valid roles
    allowed_roles = ['editor', 'author', 'reviewer', 'subscriber']
    if role not in allowed_roles:
        role = 'author'

    # Find user by email
    user = User.query.filter_by(email=email).first()

    if not user:
        flash(f'No account found for {email}. Ask them to register first.', 'warning')
        return redirect(url_for('tenants.manage_journal'))

    if user.tenant_id == tenant.id:
        flash(f'{user.full_name} is already a member of your journal.', 'info')
        return redirect(url_for('tenants.manage_journal'))

    # Add to tenant
    user.tenant_id = tenant.id
    user.role      = role
    db.session.commit()

    flash(f'âœ… {user.full_name} added as {role}!', 'success')
    return redirect(url_for('tenants.manage_journal'))

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# REMOVE MEMBER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@tenants_bp.route('/remove-member/<int:user_id>', methods=['POST'])
@login_required
@tenant_owner_required
def remove_member(user_id):
    """Remove a member from the journal"""

    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    user   = User.query.get_or_404(user_id)

    # Safety checks
    if user.id == current_user.id:
        flash('You cannot remove yourself.', 'danger')
        return redirect(url_for('tenants.manage_journal'))

    if user.tenant_id != tenant.id:
        flash('This user is not in your journal.', 'danger')
        return redirect(url_for('tenants.manage_journal'))

    user.tenant_id = None
    user.role      = 'subscriber'
    db.session.commit()

    flash(f'{user.full_name} has been removed from your journal.', 'info')
    return redirect(url_for('tenants.manage_journal'))

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# PUBLIC JOURNAL PAGE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@tenants_bp.route('/journal/<subdomain>')
def view_journal(subdomain):
    """Public page for a journal"""

    tenant = Tenant.query.filter_by(
        subdomain=subdomain,
        is_active=True
    ).first_or_404()

    return render_template('tenants/journal_public.html', tenant=tenant)

