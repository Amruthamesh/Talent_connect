#!/bin/bash

# Super Start Script for Talent Connect
# This script sets up and runs both main and documents applications

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi


print_success "All prerequisites are installed."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
# MAIN BACKEND SETUP
# ============================================================================
print_status "Setting up MAIN backend..."

print_status "Running main/backend/start.sh..."
cd "$SCRIPT_DIR/main/backend"
nohup bash start.sh > "$SCRIPT_DIR/logs/main-backend.log" 2>&1 &
MAIN_BACKEND_PID=$!
print_success "Main backend started (PID: $MAIN_BACKEND_PID)"

# ============================================================================
# DOCUMENTS BACKEND SETUP
# ============================================================================
print_status "Setting up DOCUMENTS backend..."

print_status "Running documents/backend/start.sh..."
cd "$SCRIPT_DIR/documents/backend"
nohup bash start.sh > "$SCRIPT_DIR/logs/documents-backend.log" 2>&1 &
DOCUMENTS_BACKEND_PID=$!
print_success "Documents backend started (PID: $DOCUMENTS_BACKEND_PID)"

# ============================================================================
# MAIN FRONTEND SETUP
# ============================================================================
print_status "Setting up MAIN frontend..."

cd "$SCRIPT_DIR/main/frontend"

print_status "Installing npm packages for main frontend..."
npm install
print_success "Main frontend dependencies installed"

# ============================================================================
# DOCUMENTS FRONTEND SETUP
# ============================================================================
print_status "Setting up DOCUMENTS frontend..."

cd "$SCRIPT_DIR/documents/frontend"

print_status "Installing npm packages for documents frontend..."
npm install
print_success "Documents frontend dependencies installed"

# ============================================================================
# START ALL SERVERS
# ============================================================================
print_status "Starting all servers..."

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Wait a bit for backends to start
sleep 3

# Start MAIN frontend (port 6173)
print_status "Starting MAIN frontend on port 6173..."
cd "$SCRIPT_DIR/main/frontend"
nohup npm run dev > "$SCRIPT_DIR/logs/main-frontend.log" 2>&1 &
MAIN_FRONTEND_PID=$!
print_success "Main frontend started (PID: $MAIN_FRONTEND_PID)"

# Start DOCUMENTS frontend (port 6174)
print_status "Starting DOCUMENTS frontend on port 6174..."
cd "$SCRIPT_DIR/documents/frontend"
nohup npm run dev > "$SCRIPT_DIR/logs/documents-frontend.log" 2>&1 &
DOCUMENTS_FRONTEND_PID=$!
print_success "Documents frontend started (PID: $DOCUMENTS_FRONTEND_PID)"

# Wait for frontends to start
sleep 3

# Save PIDs to file for easy stopping later
cd "$SCRIPT_DIR"
cat > .pids << EOF
MAIN_BACKEND_PID=$MAIN_BACKEND_PID
DOCUMENTS_BACKEND_PID=$DOCUMENTS_BACKEND_PID
MAIN_FRONTEND_PID=$MAIN_FRONTEND_PID
DOCUMENTS_FRONTEND_PID=$DOCUMENTS_FRONTEND_PID
EOF

print_success "All PIDs saved to .pids file"

# ============================================================================
# OPEN BROWSERS
# ============================================================================
print_status "Opening applications in browser..."

# Check if running in WSL
if grep -qi microsoft /proc/version; then
    print_status "WSL detected, opening browsers with Windows browser..."
    
    # Open main frontend
    cmd.exe /c start http://localhost:6173 2>/dev/null &
    
    
    print_success "Browsers opened"
else
    print_warning "Not running in WSL. Opening with default browser..."
    
    # Try xdg-open for Linux
    if command_exists xdg-open; then
        xdg-open http://localhost:6173     else
        print_warning "Could not auto-open browsers. Please open manually:"
        echo "  MAIN:      http://localhost:6173"
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "========================================================================"
print_success "🚀 TALENT CONNECT IS NOW RUNNING! 🚀"
echo "========================================================================"
echo ""
echo "📦 MAIN Application:"
echo "   Frontend:  http://localhost:6173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "📄 DOCUMENTS Application:"
echo "   Frontend:  http://localhost:6174"
echo "   Backend:   http://localhost:8001"
echo "   API Docs:  http://localhost:8001/api/v1/docs"
echo ""
echo "📋 Process IDs:"
echo "   Main Backend:      $MAIN_BACKEND_PID"
echo "   Documents Backend: $DOCUMENTS_BACKEND_PID"
echo "   Main Frontend:     $MAIN_FRONTEND_PID"
echo "   Documents Frontend: $DOCUMENTS_FRONTEND_PID"
echo ""
echo "📝 Logs are being written to: $SCRIPT_DIR/logs/"
echo ""
echo "To stop all servers, run: ./stop-all.sh"
echo "To view logs: tail -f logs/<service-name>.log"
echo "========================================================================"
echo ""
