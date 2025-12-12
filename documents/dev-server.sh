#!/bin/bash

# Development Server Manager for Talent Connect
# Usage: ./dev-server.sh [start|stop|restart|status]

BACKEND_DIR="/home/amramesh/wsl/Talent_Connect/backend"
FRONTEND_DIR="/home/amramesh/wsl/Talent_Connect/frontend"
BACKEND_LOG="/tmp/backend.log"
FRONTEND_LOG="/tmp/frontend.log"
BACKEND_PORT=8000
FRONTEND_PORT=6173

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

status() {
    echo -e "${YELLOW}=== Server Status ===${NC}"
    
    # Check backend
    if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend running on port $BACKEND_PORT${NC}"
        echo "  URL: http://localhost:$BACKEND_PORT/api/v1/docs"
    else
        echo -e "${RED}✗ Backend not running${NC}"
    fi
    
    # Check frontend
    if lsof -i :$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend running on port $FRONTEND_PORT${NC}"
        echo "  URL: http://localhost:$FRONTEND_PORT"
    else
        echo -e "${RED}✗ Frontend not running${NC}"
    fi
    
    echo ""
    echo "Backend log: tail -f $BACKEND_LOG"
    echo "Frontend log: tail -f $FRONTEND_LOG"
}

stop() {
    echo -e "${YELLOW}Stopping servers...${NC}"
    
    # Kill backend
    pkill -f "uvicorn app.main:app"
    
    # Kill frontend
    pkill -f "vite|npm run dev"
    
    sleep 2
    echo -e "${GREEN}Servers stopped${NC}"
}

start() {
    echo -e "${YELLOW}Starting servers...${NC}"
    
    # Start backend
    cd "$BACKEND_DIR"
    nohup ./start.sh > "$BACKEND_LOG" 2>&1 &
    echo "Backend starting... (log: $BACKEND_LOG)"
    
    # Wait for backend to start (up to 20s)
    for i in {1..20}; do
        if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Start frontend
    cd "$FRONTEND_DIR"
    nohup npm run dev -- --host > "$FRONTEND_LOG" 2>&1 &
    echo "Frontend starting... (log: $FRONTEND_LOG)"
    
    # Wait for frontend to start (up to 20s)
    for i in {1..20}; do
        if lsof -i | grep -q "localhost:$FRONTEND_PORT .*LISTEN"; then
            break
        fi
        # Detect port change from log and update FRONTEND_PORT
        if grep -q "Local:\s\+http://localhost:" "$FRONTEND_LOG"; then
            NEW_PORT=$(grep -o "Local:\s\+http://localhost:[0-9]\+" "$FRONTEND_LOG" | tail -1 | grep -o "[0-9]\+")
            if [ -n "$NEW_PORT" ] && [ "$NEW_PORT" != "$FRONTEND_PORT" ]; then
                FRONTEND_PORT=$NEW_PORT
            fi
        fi
        sleep 1
    done
    
    status
}

restart() {
    stop
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
