#!/usr/bin/env bash
# run.sh — Launch gaz_eye Flask development server
# Usage: ./run.sh

set -e

source .venv/bin/activate

# Warn if API key is missing (python-dotenv loads .env inside the app)
if [ -z "${GOOGLE_MAPS_API_KEY}" ]; then
    echo "⚠ WARNING: GOOGLE_MAPS_API_KEY is not set. Route planning will not work."
fi

export FLASK_APP=app.py
export FLASK_DEBUG=1

flask run --debug
