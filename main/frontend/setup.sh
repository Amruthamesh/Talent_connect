#!/bin/bash

# Talent Connect Frontend - Quick Start Script

echo "🚀 Setting up Talent Connect Frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js version: $(node -v)"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys"
    echo ""
fi

# Create public directory if needed
if [ ! -d public ]; then
    mkdir public
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📚 Quick Start Guide:"
echo "-------------------"
echo "1. Edit .env file with your API keys"
echo "2. Run: npm run dev"
echo "3. Visit: http://localhost:3000"
echo ""
echo "🔐 Demo Accounts:"
echo "-------------------"
echo "HR Manager:      hr@talent.com / hr123"
echo "Hiring Manager:  manager@talent.com / mgr123"
echo "Recruiter:       recruiter@talent.com / rec123"
echo ""
echo "📖 Documentation:"
echo "-------------------"
echo "- README.md                - General documentation"
echo "- AI_INTEGRATION_GUIDE.md  - AI implementation guide"
echo "- PROJECT_SUMMARY.md       - Complete overview"
echo ""
echo "🎯 Ready for your hackathon! Good luck! 🚀"
