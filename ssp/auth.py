from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Users
from . import db, bcrypt
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role_id == 1:
            return redirect(url_for('student.home'))
        elif current_user.role_id == 2:
            return redirect(url_for('ssp.ssp_index'))
        elif current_user.role_id == 3:
            return redirect(url_for('admin.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()

        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash(f'Welcome back, {user.name}!', 'success')
                if user.role_id == 1:
                    return redirect(url_for('student.home'))
                elif user.role_id == 2:
                    return redirect(url_for('ssp.ssp_index'))
                elif user.role_id == 3:
                    return redirect(url_for('admin.home'))
            else:
                flash('Invalid password.', 'danger')
        else:
            flash('No account found with that email.', 'danger')

    return render_template("login.html")


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        role_mapping = {'student': 1, 'service_professional': 2}
        role_id = role_mapping.get(role)

        if not all([name, email, password, confirm_password, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if role_id is None:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        if len(name) < 2:
            flash('Name must be at least 2 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register'))

        user = Users.query.filter_by(email=email).first()
        if user:
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        is_verified = True if role_id == 1 else False  # Students auto-verified, SPs need admin approval

        new_user = Users(
            name=name,
            email=email,
            password=hashed_password,
            role_id=role_id,
            is_verified=is_verified
        )
        db.session.add(new_user)
        db.session.commit()

        if role_id == 2:
            flash('Account created! Please wait for admin verification before logging in.', 'success')
        else:
            flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template("register.html")


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Step 1: User enters their email to identify their account."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = Users.query.filter_by(email=email).first()

        if not user:
            # Do not reveal whether email exists (security best practice)
            flash('If that email is registered, you can now reset your password.', 'info')
            return redirect(url_for('auth.reset_password', email=email))

        # Redirect to reset page with the email as a query param
        return redirect(url_for('auth.reset_password', email=email))

    return render_template('forgot_password.html')


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Step 2: User enters new password (verified by knowing their registered email)."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    email = request.args.get('email', '') or request.form.get('email', '')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email:
            flash('Email is required.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('resetpass.html', email=email)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('resetpass.html', email=email)

        user = Users.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('resetpass.html', email=email)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
