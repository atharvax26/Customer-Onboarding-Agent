@echo off
echo ========================================
echo DIAGNOSTIC TEST - Customer Onboarding Agent
echo ========================================
echo.

set ERROR_COUNT=0

echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Python is not installed or not in PATH
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo [PASS] Python is installed
)
echo.

echo [2/10] Checking Node.js installation...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Node.js is not installed or not in PATH
    set /a ERROR_COUNT+=1
) else (
    node --version
    echo [PASS] Node.js is installed
)
echo.

echo [3/10] Checking backend directory...
if exist "backend\main.py" (
    echo [PASS] Backend directory exists
) else (
    echo [FAIL] Backend directory or main.py not found
    set /a ERROR_COUNT+=1
)
echo.

echo [4/10] Checking frontend directory...
if exist "frontend\package.json" (
    echo [PASS] Frontend directory exists
) else (
    echo [FAIL] Frontend directory or package.json not found
    set /a ERROR_COUNT+=1
)
echo.

echo [5/10] Checking backend dependencies...
cd backend
python -c "import uvicorn" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Backend dependencies not installed
    echo [FIX] Run: cd backend ^& pip install -r requirements.txt
    set /a ERROR_COUNT+=1
) else (
    echo [PASS] Backend dependencies installed
)
cd ..
echo.

echo [6/10] Checking frontend dependencies...
if exist "frontend\node_modules" (
    echo [PASS] Frontend dependencies installed
) else (
    echo [FAIL] Frontend dependencies not installed
    echo [FIX] Run: cd frontend ^& npm install
    set /a ERROR_COUNT+=1
)
echo.

echo [7/10] Checking environment variables...
if exist "backend\.env" (
    echo [PASS] Backend .env file exists
) else (
    echo [FAIL] Backend .env file not found
    echo [FIX] Copy .env.example to backend\.env
    set /a ERROR_COUNT+=1
)
echo.

echo [8/10] Testing backend imports...
cd backend
python -c "from main import app; print('[PASS] Backend can import successfully')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Backend has import errors
    echo [FIX] Check backend logs above
    set /a ERROR_COUNT+=1
)
cd ..
echo.

echo [9/10] Checking ports availability...
netstat -ano | findstr ":8000" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [WARN] Port 8000 is already in use
    echo [INFO] You may need to stop the existing process
) else (
    echo [PASS] Port 8000 is available
)
echo.

netstat -ano | findstr ":5173" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [WARN] Port 5173 is already in use
    echo [INFO] You may need to stop the existing process
) else (
    echo [PASS] Port 5173 is available
)
echo.

echo [10/10] Checking database...
if exist "backend\customer_onboarding.db" (
    echo [INFO] Database file exists
) else (
    echo [INFO] Database will be created on first run
)
echo.

echo ========================================
echo DIAGNOSTIC SUMMARY
echo ========================================
if %ERROR_COUNT% EQU 0 (
    echo [SUCCESS] All checks passed! Ready to start.
    echo.
    echo Next steps:
    echo 1. Double-click start-backend.bat
    echo 2. Double-click start-frontend.bat
    echo 3. Open http://localhost:5173
) else (
    echo [FAILED] Found %ERROR_COUNT% error(s)
    echo.
    echo Please fix the errors above before starting.
)
echo ========================================
echo.
pause
