#!/bin/bash

echo "Starting backend server (Uvicorn)..."
# Start backend in the background, redirect output to backend.log
uvicorn api.main:app --host 0.0.0.0 --port 8124 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid # Save backend PID to file
echo "Backend server started with PID: $BACKEND_PID (Logs: backend.log, PID File: backend.pid)"

echo "Starting frontend server (Next.js)..."
# Start frontend in the background, redirect output to frontend.log
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd .. # Go back to root directory
echo $FRONTEND_PID > frontend.pid # Save frontend PID to file
echo "Frontend server started with PID: $FRONTEND_PID (Logs: frontend.log, PID File: frontend.pid)"

echo ""
echo "Both servers are starting in the background."
echo "Backend logs: backend.log"
echo "Frontend logs: frontend.log"
echo "Frontend should be available at http://localhost:3000 (or the next available port)"
echo "Press Ctrl+C to stop this script (this will NOT stop the background servers)."
echo "To stop the servers, run: ./stop-dev.sh" # Updated stop instruction

# Keep the script running briefly to show messages, or use 'wait' if needed
# sleep 1 # Optional: give servers a moment to potentially fail early

# Use 'wait' to keep the script alive until background processes finish (optional)
# Or just exit and let them run
