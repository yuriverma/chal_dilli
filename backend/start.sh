#!/bin/bash
# Startup script for Render deployment

# Debug: Print environment
echo "=== Environment Debug ==="
echo "PORT: $PORT"
echo "PWD: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# Ensure PORT is set
if [ -z "$PORT" ]; then
    echo "⚠️ WARNING: PORT environment variable is not set!"
    export PORT=8000
    echo "Using default PORT: $PORT"
else
    echo "✅ PORT is set to: $PORT"
fi

# Change to backend directory
cd "$(dirname "$0")" || exit 1

# Start uvicorn
echo "=== Starting uvicorn ==="
echo "Command: python -m uvicorn api_server:app --host 0.0.0.0 --port $PORT"
python -m uvicorn api_server:app --host 0.0.0.0 --port "$PORT"


