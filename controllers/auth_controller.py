from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import UserModel

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user and administrator login."""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('auth/login.html', username=username)

        user = UserModel.get_by_username(username)
        if not user or not UserModel.verify_password(user['password_hash'], password):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('auth/login.html', username=username)

        # Store user details in session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']

        flash(f"Welcome back, {user['full_name']}!", 'success')
        
        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new student/user registration."""
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not username or not full_name or not password:
            flash('Please fill in all required fields (Username, Full Name, Password).', 'warning')
            return render_template('auth/register.html', username=username, full_name=full_name, email=email, phone=phone)

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'warning')
            return render_template('auth/register.html', username=username, full_name=full_name, email=email, phone=phone)

        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'warning')
            return render_template('auth/register.html', username=username, full_name=full_name, email=email, phone=phone)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('auth/register.html', username=username, full_name=full_name, email=email, phone=phone)

        try:
            user_id = UserModel.create_user(
                username=username,
                password=password,
                full_name=full_name,
                email=email,
                phone=phone,
                role='user'
            )
            # Auto-login upon registration
            session.clear()
            session['user_id'] = user_id
            session['username'] = username
            session['full_name'] = full_name
            session['role'] = 'user'

            flash('Registration successful! Welcome to QueueLess.', 'success')
            return redirect(url_for('user.dashboard'))
        except ValueError as err:
            flash(str(err), 'danger')
            return render_template('auth/register.html', username=username, full_name=full_name, email=email, phone=phone)

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Clear session and log user out."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
