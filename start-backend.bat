@echo off
echo ========================================
echo Starting Customer Onboarding Backend
echo ========================================
echo.
cd backend
echo Current directory: %CD%
echo.
echo Checking Python...
python --version
echo.
echo Starting server on http://localhost:8000
echo API Docs will be at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
