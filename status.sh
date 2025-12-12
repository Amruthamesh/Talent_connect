#!/bin/bash

# Status Check Script for Talent Connect
# This script checks the status of all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_running() {
    echo -e "${GREEN}●${NC} Running"
}

print_stopped() {
    echo -e "${RED}●${NC} Stopped"
}

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "========================================================================"
echo "  TALENT CONNECT - SERVICE STATUS"
echo "========================================================================"
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check Main Backend (8000)
echo -n "📦 Main Backend (port 8000):       "
if check_port 8000; then
    print_running
    echo "   URL: http://localhost:8000/api/v1/docs"
else
    print_stopped
fi

# Check Documents Backend (8001)
echo -n "📄 Documents Backend (port 8001):  "
if check_port 8001; then
    print_running
    echo "   URL: http://localhost:8001/api/v1/docs"
else
    print_stopped
fi

# Check Main Frontend (6173)
echo -n "🌐 Main Frontend (port 6173):      "
if check_port 6173; then
    print_running
    echo "   URL: http://localhost:6173"
else
    print_stopped
fi

# Check Documents Frontend (6174)
echo -n "🌐 Documents Frontend (port 6174): "
if check_port 6174; then
    print_running
    echo "   URL: http://localhost:6174"
else
    print_stopped
fi

echo ""
echo "========================================================================"
echo ""

# Show PIDs if file exists
if [ -f ".pids" ]; then
    source .pids
    echo "Process IDs (from .pids file):"
    echo "  Main Backend:      $MAIN_BACKEND_PID"
    echo "  Documents Backend: $DOCUMENTS_BACKEND_PID"
    echo "  Main Frontend:     $MAIN_FRONTEND_PID"
    echo "  Documents Frontend: $DOCUMENTS_FRONTEND_PID"
    echo ""
fi

# Check logs
if [ -d "logs" ]; then
    echo "Recent logs available in: $SCRIPT_DIR/logs/"
    echo "  - main-backend.log"
    echo "  - documents-backend.log"
    echo "  - main-frontend.log"
    echo "  - documents-frontend.log"
    echo ""
fi
