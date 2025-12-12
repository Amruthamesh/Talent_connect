#!/bin/bash

# Talent Connect Backend - Development Server Startup Script

echo "🚀 Starting Talent Connect Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Always seed/init the database
echo "🗄️  Seeding/initializing database with demo accounts..."
python -m app.db.init_db

# Start the server
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/v1/docs"
echo ""
uvicorn app.main:app --reload --port 8000
