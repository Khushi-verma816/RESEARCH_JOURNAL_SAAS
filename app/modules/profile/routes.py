
# app/modules/profile/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.modules.profile import profile_bp
from app.models.user import User
from app.core.extensions import db

@profile_bp.route('/profile')
@login_required
def view():
    return render_template('profile/view.html', user=current_user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name  = request.form.get('last_name', '').strip()
        current_user.bio        = request.form.get('bio', '').strip()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view'))
    return render_template('profile/edit.html', user=current_user)

@profile_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw  = request.form.get('current_password')
    new_pw      = request.form.get('new_password')
    confirm_pw  = request.form.get('confirm_password')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile.edit'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile.edit'))

    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('profile.edit'))

    current_user.set_password(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile.view'))