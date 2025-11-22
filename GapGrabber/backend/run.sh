#!/bin/bash

# Quick start script for GapGrabber Backend

echo "🚀 Starting GapGrabber Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before running!"
fi

# Initialize database
echo "🗄️  Initializing database..."
python seed_data.py

# Start server
echo "✅ Starting FastAPI server..."
uvicorn main:app --reload --port 8000

