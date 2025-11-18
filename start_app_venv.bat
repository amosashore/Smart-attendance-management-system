@echo off
REM Activate Virtual Environment and Start Smart Attendance System

echo ============================================================
echo   Smart Attendance System (Virtual Environment)
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_venv.bat first to create it.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Checking dependencies...
python check_dependencies.py

echo.
echo ============================================================
echo   Starting Streamlit Application...
echo ============================================================
echo.
echo The browser will open automatically.
echo To stop the application, press Ctrl+C in this window.
echo.

streamlit run app.py

pause
