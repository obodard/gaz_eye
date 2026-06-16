#!/usr/bin/env bash
# run.sh — Launch checkov Flask development server
# Usage: ./run.sh

set -e

source .venv/bin/activate

# Load environment variables from .env file into the current shell
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "⚠ WARNING: .env file not found"
fi

# Warn if API keys are missing
if [ -z "${GOOGLE_MAPS_API_KEY}" ]; then
    echo "⚠ WARNING: GOOGLE_MAPS_API_KEY is not set. Route planning will not work."
fi

if [ -z "${GEMINI_API_KEY}" ]; then
    echo "⚠ WARNING: GEMINI_API_KEY is not set. Chat will not work."
fi

export FLASK_APP=app.py
export FLASK_DEBUG=1
export GEMINI_API_KEY
export GOOGLE_MAPS_API_KEY

# Start ADK agent service in background
adk api_server agent --port 5001 &
ADK_PID=$!
trap "kill $ADK_PID 2>/dev/null" EXIT

flask --app app run --debug
