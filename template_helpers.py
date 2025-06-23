from flask import current_app
from models import User


def get_user_by_id(user_id):
    """Helper function to get user by ID for templates"""
    try:
        return User.query.get(user_id)
    except:
        return None


def init_template_helpers(app):
    """Initialize template helper functions"""

    @app.context_processor
    def inject_helpers():
        """Inject helper functions into all templates"""
        return {
            'get_user_by_id': get_user_by_id
        }