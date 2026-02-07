@echo off
title Customer Onboarding Agent - Quick Start
color 0A

echo.
echo  ========================================
echo    CUSTOMER ONBOARDING AGENT
echo    Quick Start Launcher
echo  ========================================
echo.
echo  This will:
echo  1. Check your system
echo  2. Install dependencies if needed
echo  3. Start both servers
echo  4. Open your browser
echo.
echo  Press any key to continue...
pause >nul

cls
echo.
echo  Checking system...
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found!
    echo  Please install Python 3.11+ from python.org
    echo.
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Node.js not found!
    echo  Please install Node.js from nodejs.org
    echo.
    pause
    exit /b 1
)

echo  [OK] Python and Node.js found
echo.

REM Check if dependencies are installed
echo  Checking dependencies...
cd backend
python -c "import uvicorn" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  Installing backend dependencies...
    python -m pip install -q -r requirements.txt
)
cd ..

if not exist "frontend\node_modules" (
    echo  Installing frontend dependencies...
    cd frontend
    call npm install --silent
    cd ..
)

echo  [OK] Dependencies ready
echo.

REM Create directories
cd backend
if not exist "static\assets" mkdir "static\assets" >nul 2>&1
if not exist "logs" mkdir "logs" >nul 2>&1
cd ..

REM Check env file
if not exist "backend\.env" (
    if exist ".env.example" (
        copy ".env.example" "backend\.env" >nul
    )
)

cls
echo.
echo  ========================================
echo    STARTING SERVERS
echo  ========================================
echo.
echo  Opening backend server...
start "Backend - Customer Onboarding" cmd /k "cd /d "%~dp0backend" && echo Starting backend on http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo  Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo  Opening frontend server...
start "Frontend - Customer Onboarding" cmd /k "cd /d "%~dp0frontend" && echo Starting frontend on http://localhost:5173 && echo. && npm run dev"

echo  Waiting for frontend to initialize...
timeout /t 5 /nobreak >nul

cls
echo.
echo  ========================================
echo    SERVERS ARE STARTING!
echo  ========================================
echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo.
echo  Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

start http://localhost:5173

echo.
echo  ========================================
echo    SUCCESS!
echo  ========================================
echo.
echo  Your app should open in your browser.
echo  If not, manually open: http://localhost:5173
echo.
echo  Two server windows are running:
echo  - Backend Server (port 8000)
echo  - Frontend Server (port 5173)
echo.
echo  Keep those windows open while using the app.
echo  Press Ctrl+C in each window to stop.
echo.
echo  Press any key to close this launcher...
pause >nul
