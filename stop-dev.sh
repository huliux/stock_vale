#!/bin/bash

echo "Stopping development servers..."

# Check and kill backend server
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        # Optional: Add a small delay and check if killed, force kill if needed
        sleep 1
        if ps -p $BACKEND_PID > /dev/null; then
            echo "Backend server did not stop gracefully, forcing kill..."
            kill -9 $BACKEND_PID
        fi
        rm backend.pid
        echo "Backend server stopped."
    else
        echo "Backend server (PID: $BACKEND_PID) not found or already stopped."
        rm backend.pid # Clean up pid file anyway
    fi
else
    echo "Backend PID file (backend.pid) not found."
fi

# Check and kill frontend server
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        # Optional: Add a small delay and check if killed, force kill if needed
        sleep 1
        if ps -p $FRONTEND_PID > /dev/null; then
            echo "Frontend server did not stop gracefully, forcing kill..."
            kill -9 $FRONTEND_PID
        fi
        rm frontend.pid
        echo "Frontend server stopped."
    else
        echo "Frontend server (PID: $FRONTEND_PID) not found or already stopped."
        rm frontend.pid # Clean up pid file anyway
    fi
else
    echo "Frontend PID file (frontend.pid) not found."
fi

# Optional: Clean up log files
# echo "Cleaning up log files..."
# rm -f backend.log frontend.log

echo "Stop script finished."
