from flask import Blueprint, jsonify, session
from models.token_model import TokenModel
from models.service_model import ServiceModel

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/token/<int:token_id>/status')
def token_status(token_id):
    """
    Live API endpoint returning real-time queue position,
    estimated wait time, and current counter status for a token.
    Used for live polling in user digital ticket view.
    """
    token_details = TokenModel.get_queue_details(token_id)
    if not token_details:
        return jsonify({'success': False, 'message': 'Token not found'}), 404

    token = token_details['token']

    # Security check: must be logged in as user or admin
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if token['user_id'] != session['user_id'] and session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    return jsonify({
        'success': True,
        'token_id': token['id'],
        'token_number': token['token_number'],
        'service_id': token['service_id'],
        'service_name': token['service_name'],
        'status': token_details['status'],
        'position': token_details['position'],
        'position_label': token_details['position_label'],
        'people_ahead': token_details['people_ahead'],
        'estimated_wait_minutes': token_details['estimated_wait_minutes'],
        'estimated_wait_text': token_details['estimated_wait_text'],
        'current_serving': token_details['current_serving'],
        'called_at': str(token['called_at']) if token['called_at'] else None,
        'completed_at': str(token['completed_at']) if token['completed_at'] else None,
        'cancelled_at': str(token['cancelled_at']) if token['cancelled_at'] else None
    })

@api_bp.route('/services/summary')
def services_summary():
    """Live API returning current waiting and serving status for all active services."""
    services = ServiceModel.get_services_with_metrics()
    summary = []
    for s in services:
        summary.append({
            'id': s['id'],
            'service_code': s['service_code'],
            'service_name': s['service_name'],
            'waiting_count': s['waiting_count'],
            'current_serving': s['current_serving'] or 'None',
            'is_active': s['is_active']
        })
    return jsonify({'success': True, 'services': summary})
