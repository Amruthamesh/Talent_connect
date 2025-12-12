#!/bin/bash

# Stop All Script for Talent Connect
# This script stops all running services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_status "Stopping Talent Connect services..."

# Check if .pids file exists
if [ -f ".pids" ]; then
    source .pids
    
    # Stop each process if it's running
    if [ ! -z "$MAIN_BACKEND_PID" ] && kill -0 $MAIN_BACKEND_PID 2>/dev/null; then
        print_status "Stopping main backend (PID: $MAIN_BACKEND_PID)..."
        kill $MAIN_BACKEND_PID
        print_success "Main backend stopped"
    else
        print_warning "Main backend is not running"
    fi
    
    if [ ! -z "$DOCUMENTS_BACKEND_PID" ] && kill -0 $DOCUMENTS_BACKEND_PID 2>/dev/null; then
        print_status "Stopping documents backend (PID: $DOCUMENTS_BACKEND_PID)..."
        kill $DOCUMENTS_BACKEND_PID
        print_success "Documents backend stopped"
    else
        print_warning "Documents backend is not running"
    fi
    
    if [ ! -z "$MAIN_FRONTEND_PID" ] && kill -0 $MAIN_FRONTEND_PID 2>/dev/null; then
        print_status "Stopping main frontend (PID: $MAIN_FRONTEND_PID)..."
        kill $MAIN_FRONTEND_PID
        print_success "Main frontend stopped"
    else
        print_warning "Main frontend is not running"
    fi
    
    if [ ! -z "$DOCUMENTS_FRONTEND_PID" ] && kill -0 $DOCUMENTS_FRONTEND_PID 2>/dev/null; then
        print_status "Stopping documents frontend (PID: $DOCUMENTS_FRONTEND_PID)..."
        kill $DOCUMENTS_FRONTEND_PID
        print_success "Documents frontend stopped"
    else
        print_warning "Documents frontend is not running"
    fi
    
    # Remove .pids file
    rm .pids
    print_success "PIDs file removed"
else
    print_warning "No .pids file found. Attempting to kill by port..."
    
    # Kill processes by port as fallback
    print_status "Checking port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null && print_success "Killed process on port 8000" || print_warning "No process on port 8000"
    
    print_status "Checking port 8001..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null && print_success "Killed process on port 8001" || print_warning "No process on port 8001"
    
    print_status "Checking port 6173..."
    lsof -ti:6173 | xargs kill -9 2>/dev/null && print_success "Killed process on port 6173" || print_warning "No process on port 6173"
    
    print_status "Checking port 6174..."
    lsof -ti:6174 | xargs kill -9 2>/dev/null && print_success "Killed process on port 6174" || print_warning "No process on port 6174"
fi

echo ""
print_success "✅ All Talent Connect services stopped"
echo ""
