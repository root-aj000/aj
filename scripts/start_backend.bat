@echo off
REM Start Backend Script for Vibe Agent (Windows)

echo Starting Vibe Agent Backend...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist "..\..env" (
    echo .env file not found!
    echo Copying from .env.example...
    copy ..\.env.example ..\.env
    echo Please edit .env with your configuration before continuing.
    exit /b 1
)

echo All dependencies ready
echo.

REM Start FastAPI server
echo Starting FastAPI server on http://localhost:8000
echo API docs will be available at http://localhost:8000/docs
echo.

uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
