@echo off
echo Testing backend startup...
cd backend
python -c "from main import app; print('✓ Backend can start successfully!')"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Backend is ready to run.
    echo ========================================
    echo.
    echo To start the backend, run: start-backend.bat
    echo Or manually: cd backend ^& python -m uvicorn main:app --reload
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR! Backend has issues.
    echo ========================================
    echo.
    echo Please check the error message above.
)
pause
