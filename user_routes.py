from flask import Blueprint, render_template, redirect, url_for, flash, request
from forms import LoginForm
from models import User
from werkzeug.security import check_password_hash
from flask_login import login_user, current_user, logout_user, login_required

"""
Tworzymy blueprint dla tras użytkownika.
"""
user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET', 'POST'])
@user_bp.route('/login', methods=['GET', 'POST']) # Trasa logowania
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('user.dashboard'))
        else:
            flash('Błędny login lub hasło.', 'danger')
    return render_template('login.html', form=form)

# Trasa pulpitu użytkownika (admin dashboard oraz user dashboard)
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('user_dashboard.html', username=current_user.username)

# Trasa wylogowania
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))
