from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from controllers import admin_required
from models.service_model import ServiceModel
from models.token_model import TokenModel
from models.user_model import UserModel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin main command dashboard with service counters, stats, and live queue controls."""
    stats = TokenModel.get_admin_stats()
    services_with_metrics = ServiceModel.get_services_with_metrics()
    
    # Optional filter by service in query params
    selected_service_id = request.args.get('service_id', type=int)
    status_filter = request.args.get('status', default=None)

    # By default, show active (Serving, Waiting) tokens
    queue_tokens = TokenModel.get_service_queue(
        service_id=selected_service_id,
        status_filter=status_filter if status_filter else None,
        limit=100
    )

    all_services = ServiceModel.get_all(active_only=False)

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        services=services_with_metrics,
        all_services=all_services,
        queue_tokens=queue_tokens,
        selected_service_id=selected_service_id,
        status_filter=status_filter
    )

@admin_bp.route('/call-next', methods=['POST'])
@admin_required
def call_next():
    """Admin calls the next waiting token for a service counter."""
    service_id = request.form.get('service_id', type=int)
    if not service_id:
        flash('Please select a valid service.', 'warning')
        return redirect(url_for('admin.dashboard'))

    service = ServiceModel.get_by_id(service_id)
    if not service:
        flash('Service not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    called_token = TokenModel.call_next(service_id)
    if called_token:
        flash(f"Now Serving: {called_token['token_number']} at {service['service_name']} counter!", 'success')
    else:
        flash(f"No tokens currently waiting for {service['service_name']}.", 'info')

    return redirect(url_for('admin.dashboard', service_id=service_id))

@admin_bp.route('/token/<int:token_id>/action', methods=['POST'])
@admin_required
def token_action():
    """Admin manual status action on an individual token (Complete, Cancel, Serve)."""
    action = request.form.get('action')
    notes = request.form.get('notes', '').strip()
    return_url = request.form.get('return_url') or url_for('admin.dashboard')

    token = TokenModel.get_by_id(token_id)
    if not token:
        flash('Token not found.', 'danger')
        return redirect(return_url)

    try:
        if action == 'complete':
            TokenModel.update_status(token_id, 'Completed', notes or 'Completed by admin')
            flash(f"Token {token['token_number']} marked as Completed.", 'success')
        elif action == 'cancel':
            TokenModel.update_status(token_id, 'Cancelled', notes or 'Cancelled by admin')
            flash(f"Token {token['token_number']} has been Cancelled.", 'warning')
        elif action == 'serve':
            TokenModel.update_status(token_id, 'Serving', notes or 'Called to counter by admin')
            flash(f"Token {token['token_number']} is now being served.", 'success')
        else:
            flash(f"Unknown action: {action}", 'danger')
    except Exception as e:
        flash(f"Error performing action: {str(e)}", 'danger')

    return redirect(return_url)

@admin_bp.route('/services', methods=['GET', 'POST'])
@admin_required
def manage_services():
    """Admin view to manage, create, and update service counters."""
    if request.method == 'POST':
        action = request.form.get('form_action', 'create')
        
        if action == 'create':
            service_code = request.form.get('service_code', '').strip()
            service_name = request.form.get('service_name', '').strip()
            description = request.form.get('description', '').strip()
            avg_wait = request.form.get('avg_wait_per_token', 5)
            prefix = request.form.get('prefix', '').strip()

            if not service_code or not service_name:
                flash('Service Code and Service Name are required.', 'warning')
            else:
                try:
                    ServiceModel.create(service_code, service_name, description, avg_wait, prefix)
                    flash(f"Service '{service_name}' ({service_code}) created successfully!", 'success')
                    return redirect(url_for('admin.manage_services'))
                except ValueError as ve:
                    flash(str(ve), 'danger')
                except Exception as e:
                    flash(f"Failed to create service: {str(e)}", 'danger')

        elif action == 'update':
            service_id = request.form.get('service_id', type=int)
            service_name = request.form.get('service_name', '').strip()
            description = request.form.get('description', '').strip()
            avg_wait = request.form.get('avg_wait_per_token', 5)
            prefix = request.form.get('prefix', '').strip()

            if not service_id or not service_name:
                flash('Invalid data for updating service.', 'warning')
            else:
                try:
                    ServiceModel.update(service_id, service_name, description, avg_wait, prefix)
                    flash('Service updated successfully!', 'success')
                    return redirect(url_for('admin.manage_services'))
                except Exception as e:
                    flash(f"Failed to update service: {str(e)}", 'danger')

    services = ServiceModel.get_services_with_metrics()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/services/<int:service_id>/toggle', methods=['POST'])
@admin_required
def toggle_service(service_id):
    """Toggle a service counter active/inactive."""
    new_status = ServiceModel.toggle_status(service_id)
    status_label = 'Activated' if new_status == 1 else 'Deactivated'
    flash(f"Service status changed to {status_label}.", 'info')
    return redirect(url_for('admin.manage_services'))

@admin_bp.route('/history')
@admin_required
def queue_history():
    """View full audit history of all tokens with search and filter."""
    service_id = request.args.get('service_id', type=int)
    status_filter = request.args.get('status', default=None)
    
    tokens = TokenModel.get_service_queue(service_id=service_id, status_filter=status_filter, limit=200)
    services = ServiceModel.get_all(active_only=False)

    return render_template(
        'admin/queue_history.html',
        tokens=tokens,
        services=services,
        selected_service_id=service_id,
        status_filter=status_filter
    )
