@echo off
echo Starting Traffic Violation Detection System...
echo.

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

cd app
python main.py
