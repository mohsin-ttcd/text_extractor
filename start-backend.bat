@echo off
echo Starting Backend (port 8000)...
cd /d "%~dp0"
python backend/run.py
pause
