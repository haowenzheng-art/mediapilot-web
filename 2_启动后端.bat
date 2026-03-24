
@echo off
cd /d "%~dp0backend"
echo Starting MediaPilot Backend...
echo.
echo API docs: http://localhost:8000/docs
echo.
"C:\Users\19802\anaconda3\python.exe" main_full.py
pause

