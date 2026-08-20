@echo off
title Expense Tracker - install dependencies
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

echo Installing dependencies (easyocr, opencv, pillow, matplotlib)...
%PY% -m pip install -r requirements.txt
echo.
echo Done. Double-click run.bat to start the app.
pause
