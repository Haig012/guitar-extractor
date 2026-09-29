@echo off
setlocal EnableExtensions
title Guitar Extractor - Setup
cd /d "%~dp0"

echo ============================================
echo  Guitar Extractor - Setup
echo  Made by Hai Guriel
echo ============================================
echo.
echo This creates a private Python environment in this folder (.venv),
echo installs everything the app needs into it, and checks for FFmpeg.
echo Nothing is installed into your system Python.
echo.

REM ---- 1. Find Python 3.10-3.12 (PyTorch 2.5 has no wheels for 3.13+) ----
set "PY="
for %%V in (3.11 3.12 3.10) do (
    if not defined PY (
        py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [ERROR] Python 3.10, 3.11 or 3.12 was not found.
    echo.
    echo Install Python 3.11 from https://www.python.org/downloads/release/python-3119/
    echo   ^(or: winget install Python.Python.3.11^)
    echo and tick "Add python.exe to PATH" in the installer. Then run this again.
    echo Python 3.13 and newer will NOT work yet ^(no PyTorch builds for them^).
    goto :fail
)
for /f "delims=" %%i in ('%PY% -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%i"
echo [OK] Using Python %PYVER%  ^(%PY%^)
echo.

REM ---- 2. Private environment ----
if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv ...
    %PY% -m venv .venv
    if errorlevel 1 goto :fail
)
set "VPY=%~dp0.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
echo.

REM ---- 3. PyTorch: CUDA build if there is an NVIDIA GPU ----
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [GPU] NVIDIA GPU found - installing the CUDA build of PyTorch.
    echo       This is a large download ^(about 2.5 GB^) and can take a while.
    "%VPY%" -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
    if errorlevel 1 goto :fail
) else (
    echo [CPU] No NVIDIA GPU found - using the CPU build of PyTorch.
    echo       Everything works; separating a song just takes longer.
)
echo.

REM ---- 4. Everything else ----
echo Installing the app's dependencies...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo.

REM ---- 5. FFmpeg ----
"%VPY%" -c "import sys; sys.path.insert(0, '.'); from pipeline.worker import _find_ffmpeg; sys.exit(0 if _find_ffmpeg() else 1)" >nul 2>&1
if not errorlevel 1 (
    echo [OK] FFmpeg found.
) else (
    echo [!] FFmpeg was not found - the app needs it.
    where winget >nul 2>&1
    if not errorlevel 1 (
        choice /M "Install FFmpeg now with winget"
        if not errorlevel 2 (
            winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        )
    ) else (
        echo Download it from https://ffmpeg.org/download.html and add its bin folder to PATH.
    )
)

echo.
echo ============================================
echo  Setup complete. Start the app with run.bat
echo ============================================
pause
exit /b 0

:fail
echo.
echo ============================================
echo  Setup did not finish - see the message above.
echo ============================================
pause
exit /b 1
