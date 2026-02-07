@echo off
echo ========================================
echo Starting Customer Onboarding Frontend
echo ========================================
echo.
cd frontend
echo Current directory: %CD%
echo.
echo Checking Node...
node --version
echo.
echo Installing dependencies (if needed)...
call npm install
echo.
echo Starting development server...
echo Frontend will be at: http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
call npm run dev
pause
