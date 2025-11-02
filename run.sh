#!/bin/bash
# Kill any existing process on port 8001
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
sleep 1

# Start the backend server
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
