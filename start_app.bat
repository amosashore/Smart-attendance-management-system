@echo off
REM Smart Attendance System Launcher
echo ============================================================
echo   Starting Smart Attendance System...
echo ============================================================
echo.

cd /d "%~dp0"

echo Checking dependencies...
python check_dependencies.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Some dependencies are missing!
    echo The application may not work correctly.
    echo.
    pause
)

echo.
echo Starting Streamlit application...
echo The browser will open automatically.
echo.
echo To stop the application, press Ctrl+C in this window.
echo.

streamlit run app.py

pause
