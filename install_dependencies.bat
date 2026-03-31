@echo off
title Guitar Extractor — Installing Dependencies
echo ============================================
echo  Guitar Extractor — Dependency Installer
echo  Made by Hai Guriel
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found.
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing PySide6 (GUI framework)...
pip install PySide6>=6.6.0

echo.
echo Installing yt-dlp (YouTube downloader)...
pip install yt-dlp

echo.
echo Installing Demucs (stem separation)...
echo NOTE: This installs PyTorch and may take several minutes and ~2GB disk space.
pip install demucs

echo.
echo Installing soundfile (required WAV backend for torchaudio on Windows)...
pip install soundfile

echo.
echo Installing DeepFilterNet (noise cleaning)...
pip install deepfilternet

echo.
echo ============================================
echo  MANUAL STEP REQUIRED: Install ffmpeg
echo ============================================
echo.
echo Option 1 (Windows Package Manager):
echo   winget install Gyan.FFmpeg
echo.
echo Option 2 (Manual):
echo   Download from https://ffmpeg.org/download.html
echo   Extract and add to your system PATH.
echo.
echo ============================================
echo  Installation complete!
echo  Run the app with: run.bat
echo ============================================
pause
