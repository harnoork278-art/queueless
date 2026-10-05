from flask import Flask, render_template, session
from datetime import datetime
from config import Config
from models.db import close_db, init_db
from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.admin_controller import admin_bp
from controllers.api_controller import api_bp

def create_app(config_class=Config):
    """Application factory for QueueLess Virtual Queue System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register teardown handlers
    app.teardown_appcontext(close_db)

    # Register Blueprints (Controllers)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Context processor to inject user information into all templates
    @app.context_processor
    def inject_context():
        return {
            'logged_in': 'user_id' in session,
            'current_user_id': session.get('user_id'),
            'current_username': session.get('username'),
            'current_full_name': session.get('full_name'),
            'current_role': session.get('role'),
            'is_admin': session.get('role') == 'admin',
            'current_year': datetime.now().year
        }

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Auto-initialize database tables and default seed data on startup
    with app.app_context():
        init_db(app)

    return app

app = create_app()

if __name__ == '__main__':
    import os

    print("=" * 60)
    print("  QueueLess - Virtual Queue System")
    print("  Status: Server starting...")
    print("  Default Admin Login: admin / admin123")
    print("  Default Student Login: student / student123")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )