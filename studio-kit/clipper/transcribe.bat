@echo off
cd /d "%~dp0"
node check-deps.js
if errorlevel 1 ( pause & exit /b 1 )
echo.
node transcribe.js
echo.
pause
