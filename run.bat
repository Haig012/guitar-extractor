@echo off
title Guitar Extractor - Made by Hai Guriel
cd /d "%~dp0"

REM Use an existing Python venv that has GPU torch + demucs + yt-dlp.
set "VENV=C:\path\to\your\venv"

if not exist "%VENV%\Scripts\python.exe" (
    echo ERROR: Expected Python venv not found at "%VENV%".
    echo Edit run.bat and point VENV at a Python env that has demucs, torch and yt-dlp.
    pause
    exit /b 1
)

REM Put the venv Scripts on PATH so the bare "yt-dlp" call resolves.
set "PATH=%VENV%\Scripts;%PATH%"

"%VENV%\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
