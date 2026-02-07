@echo off
echo ========================================
echo AUTO-FIX AND START
echo Customer Onboarding Agent
echo ========================================
echo.

echo Step 1: Installing backend dependencies...
cd backend
echo Installing Python packages...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Backend dependencies installed
cd ..
echo.

echo Step 2: Installing frontend dependencies...
cd frontend
echo Installing Node packages (this may take a minute)...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Frontend dependencies installed
cd ..
echo.

echo Step 3: Checking environment file...
if not exist "backend\.env" (
    echo Creating .env file from example...
    copy ".env.example" "backend\.env"
    echo [WARN] Please update backend\.env with your API keys
)
echo [SUCCESS] Environment file ready
echo.

echo Step 4: Creating necessary directories...
cd backend
if not exist "static" mkdir static
if not exist "static\assets" mkdir "static\assets"
if not exist "logs" mkdir logs
echo [SUCCESS] Directories created
cd ..
echo.

echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Starting servers...
echo.

echo Opening backend in new window...
start "Backend Server" cmd /k "cd backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Opening frontend in new window...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo SERVERS STARTING!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Two new windows should have opened.
echo Wait for both to finish starting, then open:
echo.
echo    http://localhost:5173
echo.
echo Press any key to close this window...
pause >nul
