#!/bin/bash

# Default port if PORT environment variable is not set
export PORT=${PORT:-8000}

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers