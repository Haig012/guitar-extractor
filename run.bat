@echo off
setlocal
title Guitar Extractor - Made by Hai Guriel
cd /d "%~dp0"

REM Python to use: GUITAR_EXTRACTOR_PYTHON if you set one, else the .venv that
REM install_dependencies.bat creates in this folder.
if defined GUITAR_EXTRACTOR_PYTHON (
    set "PYEXE=%GUITAR_EXTRACTOR_PYTHON%"
) else (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
)

if not exist "%PYEXE%" (
    echo Guitar Extractor is not set up yet.
    echo Double-click install_dependencies.bat first ^(one time^), then run this again.
    pause
    exit /b 1
)

REM Put that environment's Scripts folder first on PATH for any helper tools.
for %%P in ("%PYEXE%") do set "PATH=%%~dpP;%PATH%"

"%PYEXE%" main.py
if errorlevel 1 (
    echo.
    echo The app exited with an error - see the message above.
    pause
)
