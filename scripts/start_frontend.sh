#!/bin/bash

# Start Frontend Script for Vibe Agent

set -e

echo "🎨 Starting Vibe Agent Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found!"
    echo "   Please run: npm install"
    exit 1
fi

echo "✅ Dependencies ready"
echo ""

# Start Next.js dev server
echo "🌐 Starting Next.js dev server on http://localhost:3000"
echo ""

npm run dev
