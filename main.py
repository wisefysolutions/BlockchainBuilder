"""
Main entry point for the Blockchain API Application.

This file serves as the entry point for running the Flask application.
"""

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
