@echo off
title Guitar Extractor - Made by Hai Guriel
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Check PySide6
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installing PySide6...
    pip install PySide6
)

python main.py
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
