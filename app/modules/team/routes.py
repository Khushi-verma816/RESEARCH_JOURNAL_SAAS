# app/modules/team/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.modules.team import team_bp
from app.models.user import User
from app.models.tenant import Tenant
from app.core.extensions import db
from app.core.decorators import tenant_owner_required

def _managed_tenant_for_current_user():
    tenant = Tenant.query.filter_by(owner_id=current_user.id).first()
    if tenant:
        return tenant
    if current_user.tenant_id:
        return Tenant.query.get(current_user.tenant_id)
    return None

@team_bp.route('/team')
@login_required
@tenant_owner_required
def index():
    # Admin users can see all users, regular tenant owners see their team
    if current_user.role == 'admin':
        # Show all authors and reviewers across platform
        members = User.query.filter(User.role.in_(['author', 'reviewer', 'editor'])).all()
        # Create a dummy tenant object for template compatibility
        tenant = type('obj', (object,), {'name': 'All Users', 'id': None})()
    else:
        tenant = _managed_tenant_for_current_user()
        if not tenant:
            flash('Create a journal first.', 'warning')
            return redirect(url_for('tenants.create_journal'))
        members = User.query.filter_by(tenant_id=tenant.id).all()
    role_priority = {
        'super_admin': 0,
        'admin': 1,
        'tenant_owner': 2,
        'editor': 3,
        'reviewer': 4,
        'author': 5,
        'subscriber': 6,
    }
    members = sorted(
        members,
        key=lambda m: (
            role_priority.get(m.role, 9),
            0 if m.id == current_user.id else 1,
            (m.first_name or '').lower(),
            (m.last_name or '').lower(),
            m.id,
        )
    )

    # Group by role
    editors   = [m for m in members if m.role in ['editor', 'tenant_owner']]
    reviewers = [m for m in members if m.role == 'reviewer']
    authors   = [m for m in members if m.role == 'author']
    others    = [m for m in members if m.role not in ['editor','tenant_owner','reviewer','author']]

    return render_template(
        'team/index.html',
        user=current_user,
        tenant=tenant,
        members=members,
        editors=editors,
        reviewers=reviewers,
        authors=authors,
        others=others,
    )

@team_bp.route('/team/invite', methods=['POST'])
@login_required
@tenant_owner_required
def invite():
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    email  = request.form.get('email', '').strip().lower()
    role   = request.form.get('role', 'author')

    if not email:
        flash('Please enter an email address.', 'danger')
        return redirect(url_for('team.index'))

    allowed_roles = ['editor', 'author', 'reviewer', 'subscriber']
    if role not in allowed_roles:
        role = 'author'

    user = User.query.filter_by(email=email).first()
    if not user:
        flash(f'No account found for {email}. Ask them to register first.', 'warning')
        return redirect(url_for('team.index'))

    if user.id == current_user.id:
        flash('You cannot invite yourself.', 'danger')
        return redirect(url_for('team.index'))

    if user.tenant_id == tenant.id:
        flash(f'{user.full_name} is already a member.', 'info')
        return redirect(url_for('team.index'))

    user.tenant_id = tenant.id
    user.role      = role
    db.session.commit()

    flash(f'✅ {user.full_name} added as {role}!', 'success')
    return redirect(url_for('team.index'))

@team_bp.route('/team/remove/<int:user_id>', methods=['POST'])
@login_required
@tenant_owner_required
def remove(user_id):
    tenant = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    user   = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot remove yourself.', 'danger')
        return redirect(url_for('team.index'))

    if user.tenant_id != tenant.id:
        flash('This user is not in your journal.', 'danger')
        return redirect(url_for('team.index'))

    user.tenant_id = None
    user.role      = 'subscriber'
    db.session.commit()

    flash(f'{user.full_name} removed from your journal.', 'info')
    return redirect(url_for('team.index'))

@team_bp.route('/team/change-role/<int:user_id>', methods=['POST'])
@login_required
@tenant_owner_required
def change_role(user_id):
    tenant  = _managed_tenant_for_current_user()
    if not tenant:
        flash('Create a journal first.', 'warning')
        return redirect(url_for('tenants.create_journal'))
    user    = User.query.get_or_404(user_id)
    new_role = request.form.get('role', 'author')

    if user.tenant_id != tenant.id:
        flash('This user is not in your journal.', 'danger')
        return redirect(url_for('team.index'))

    allowed = ['editor', 'author', 'reviewer', 'subscriber']
    if new_role in allowed:
        user.role = new_role
        db.session.commit()
        flash(f'{user.full_name} role updated to {new_role}.', 'success')

    return redirect(url_for('team.index'))
