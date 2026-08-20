@echo off
title Expense Tracker
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

%PY% main.py
if errorlevel 1 (
    echo.
    echo Failed to start. Install Python from https://www.python.org
    echo and tick "Add Python to PATH", then run install_deps.bat once.
    pause
)
