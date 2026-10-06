@echo off
set FLASK_DEV=1
"%~dp0venv\Scripts\python.exe" app.py
pause
