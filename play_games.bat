@echo off
REM Freebuff Arcade - 21 Python games in one app
cd /d "%~dp0"
python play_games.py
if errorlevel 1 pause
