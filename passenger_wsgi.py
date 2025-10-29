import os
import sys

# Ensure the application root is on the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import the Flask app as `application` for Passenger
from app import app as application

# Optional: set environment defaults suitable for Hostinger
os.environ.setdefault('FLASK_ENV', 'production')

