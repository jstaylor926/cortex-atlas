#!/bin/bash

# Atlas Quick Setup Script

echo "🚀 Setting up Atlas - Local-First Personal OS"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Prerequisites found"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your OpenAI API key"
fi

# Initialize database
echo "Initializing database..."
python -c "from atlas_api.database import init_db; init_db()"

echo "✅ Backend setup complete"
cd ..
echo ""

# Frontend setup
echo "📱 Setting up frontend..."
cd app

# Install Electron dependencies
echo "Installing Electron dependencies..."
npm install

# Install renderer dependencies
cd renderer
echo "Installing React dependencies..."
npm install
cd ..

echo "✅ Frontend setup complete"
cd ..
echo ""

echo "✨ Setup complete!"
echo ""
echo "To start development:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend && source venv/bin/activate && python uvicorn_entry.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd app/renderer && npm run dev"
echo ""
echo "Terminal 3 - Electron:"
echo "  cd app && npm run dev:electron"
echo ""
echo "Don't forget to add your OpenAI API key to backend/.env!"
