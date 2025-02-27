from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, logout_user, login_required
from models import User
from forms import CreateUserForm, ResetPasswordForm
from extensions import db
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Panel sterowania, wyświetla liste wszystkich użytkowników
@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('user.dashboard'))
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users, username=current_user.username)

# Tworzenie nowych użytkowników
@admin_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('user.dashboard'))
    form = CreateUserForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            is_admin=form.is_admin.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Użytkownik utworzony pomyślnie!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('create_user.html', form=form)

# Reset hasła użytkowników
@admin_bp.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('user.dashboard'))
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Hasło zostało zresetowane.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('reset_password.html', form=form, user=user)

@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('user.login'))
