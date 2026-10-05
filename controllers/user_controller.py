from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from controllers import login_required
from models.service_model import ServiceModel
from models.token_model import TokenModel

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    """Home / landing redirect to dashboard if logged in, else login."""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User home dashboard displaying services catalog, active tickets, and recent activity."""
    user_id = session['user_id']
    
    # Fetch active services with live queue metrics
    services = ServiceModel.get_services_with_metrics()
    
    # Fetch user tokens
    all_tokens = TokenModel.get_user_tokens(user_id)
    active_tokens = [t for t in all_tokens if t['status'] in ('Waiting', 'Serving')]
    recent_tokens = [t for t in all_tokens if t['status'] not in ('Waiting', 'Serving')][:5]

    # Calculate live queue info for active tokens
    enriched_active = []
    for t in active_tokens:
        q_info = TokenModel.get_queue_details(t['id'])
        enriched_active.append(q_info)

    return render_template(
        'user/dashboard.html',
        services=services,
        active_tokens=enriched_active,
        recent_tokens=recent_tokens
    )

@user_bp.route('/book-token', methods=['POST'])
@login_required
def book_token():
    """Book a new digital queue token for a selected service."""
    service_id = request.form.get('service_id')
    user_id = session['user_id']

    if not service_id:
        flash('Please select a valid service.', 'warning')
        return redirect(url_for('user.dashboard'))

    try:
        service_id = int(service_id)
        token_id = TokenModel.create_token(service_id, user_id)
        token = TokenModel.get_by_id(token_id)
        flash(f"Token {token['token_number']} generated successfully for {token['service_name']}!", 'success')
        return redirect(url_for('user.view_token', token_id=token_id))
    except ValueError as err:
        flash(str(err), 'danger')
        return redirect(url_for('user.dashboard'))
    except Exception as e:
        flash(f"Failed to generate token: {str(e)}", 'danger')
        return redirect(url_for('user.dashboard'))

@user_bp.route('/token/<int:token_id>')
@login_required
def view_token(token_id):
    """View digital token details with live queue position and wait estimation."""
    token_details = TokenModel.get_queue_details(token_id)
    if not token_details:
        abort(404)

    # Security check: only token owner or admin can view
    token = token_details['token']
    if token['user_id'] != session['user_id'] and session.get('role') != 'admin':
        flash('You are not authorized to view this token.', 'danger')
        return redirect(url_for('user.dashboard'))

    return render_template('user/token_view.html', details=token_details)

@user_bp.route('/token/<int:token_id>/cancel', methods=['POST'])
@login_required
def cancel_token(token_id):
    """Allow user to cancel their own active token."""
    user_id = session['user_id']
    try:
        TokenModel.cancel_token(token_id, user_id=user_id, notes="Cancelled by student via dashboard")
        flash('Your token has been successfully cancelled.', 'info')
    except ValueError as err:
        flash(str(err), 'warning')
    except Exception as e:
        flash(f"Unable to cancel token: {str(e)}", 'danger')

    return redirect(url_for('user.view_token', token_id=token_id))

@user_bp.route('/my-tokens')
@login_required
def my_tokens():
    """View all past and active tokens for the current user."""
    user_id = session['user_id']
    tokens = TokenModel.get_user_tokens(user_id)
    return render_template('user/my_tokens.html', tokens=tokens)
