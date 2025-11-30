@echo off
REM Start Frontend Script for Vibe Agent (Windows)

echo Starting Vibe Agent Frontend...
echo.

REM Check if node_modules exists
if not exist "node_modules\" (
    echo node_modules not found!
    echo Please run: npm install
    exit /b 1
)

echo Dependencies ready
echo.

REM Start Next.js dev server
echo Starting Next.js dev server on http://localhost:3000
echo.

npm run dev
