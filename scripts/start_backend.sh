#!/bin/bash

# Start Backend Script for Vibe Agent

set -e

echo "🚀 Starting Vibe Agent Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Copying from .env.example..."
    cp ../.env.example ../.env
    echo "   ⚠️  Please edit .env with your configuration before continuing."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not running!"
    echo "   Please start Redis: redis-server"
    exit 1
fi

# Check if Neo4j is accessible
if ! nc -z localhost 7687 > /dev/null 2>&1; then
    echo "⚠️  Neo4j not accessible on port 7687!"
    echo "   Please start Neo4j Desktop"
    exit 1
fi

echo "✅ All dependencies ready"
echo ""

# Start FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo ""

uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
