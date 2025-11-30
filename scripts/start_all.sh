#!/bin/bash

# Start All Services for Vibe Agent

set -e

echo "🚀 Starting Vibe Agent - All Services"
echo "======================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 not found!"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js not found!"
    exit 1
fi

if ! command_exists redis-cli; then
    echo "❌ Redis not found!"
    exit 1
fi

echo "✅ All prerequisites satisfied"
echo ""

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Check Neo4j
if ! nc -z localhost 7687 > /dev/null 2>&1; then
    echo "⚠️  Neo4j not accessible!"
    echo "   Please start Neo4j Desktop manually"
    exit 1
fi

echo "✅ All services ready"
echo ""
echo "Starting components in separate terminals..."
echo ""
echo "Please open the following in separate terminals:"
echo ""
echo "  Terminal 1 (Backend):"
echo "  $ cd backend && bash ../scripts/start_backend.sh"
echo ""
echo "  Terminal 2 (Frontend):"
echo "  $ cd frontend && bash ../scripts/start_frontend.sh"
echo ""
echo "  Terminal 3 (Optional - Celery Worker):"
echo "  $ cd backend && celery -A src.app.celery_app worker --loglevel=info"
echo ""
