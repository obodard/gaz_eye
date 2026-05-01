"""
gaz_eye — Flask application factory.

Creates and configures the Flask app. All routes are registered via Blueprint.
Zero @app.route decorators live here.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask

logger = logging.getLogger("gaz_eye")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()

    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        logger.warning("⚠ WARNING: GOOGLE_MAPS_API_KEY is not set. "
                       "Route planning will not work without a valid API key. "
                       "Add it to your .env file.")

    app = Flask(__name__, static_folder="static", template_folder="static")
    app.config["GOOGLE_MAPS_API_KEY"] = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    from api.routes import bp
    app.register_blueprint(bp)

    return app


app = create_app()
