
@echo off
cd /d "%~dp0"
echo Starting MediaPilot Backend...
echo.
echo API docs: http://localhost:8000/docs
echo.
"C:\Users\19802\anaconda3\python.exe" -m backend.main
pause

