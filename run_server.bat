@echo off
cd /d "%~dp0"
echo Starting Video Transcribe Server...
echo Logs will appear below:
call venv\Scripts\activate
start http://localhost:8010/docs
python -m app.main
pause
