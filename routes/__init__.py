"""
Routes package for PepperAI
"""
from flask import Blueprint

# Create blueprints
history_bp = Blueprint('history', __name__)
statistics_bp = Blueprint('statistics', __name__)
export_bp = Blueprint('export', __name__)
pepper_database_bp = Blueprint('pepper_database', __name__)
notifications_bp = Blueprint('notifications', __name__)

# Import route handlers
from . import history
from . import statistics
from . import export
from . import pepper_database
from . import notifications

