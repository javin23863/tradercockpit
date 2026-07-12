@echo off
REM Double-click this to run the clipper.

cd /d "%~dp0"

echo.
echo  YouTube auto-clipper
echo.

REM Check dependencies first
node check-deps.js
if errorlevel 1 (
    echo.
    echo  Install the missing dependencies above, then double-click this again.
    pause
    exit /b 1
)

echo.
node clip.js

echo.
pause
