#!/bin/bash
# Kill any existing process on port 8001 (skip if lsof is not available)
# On some Windows bash environments `lsof` isn't installed which causes a
# noisy "command not found" message; check for the command first.
if command -v lsof >/dev/null 2>&1; then
	lsof -ti :8001 | xargs kill -9 2>/dev/null || true
fi
sleep 1

# Start the backend server
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
