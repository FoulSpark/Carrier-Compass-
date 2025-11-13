@echo off
echo ========================================
echo EduPath College Directory - Port 5002
echo ========================================
echo.
echo Starting College Directory Server...
echo.

cd /d "%~dp0"
python start_college_app.py

echo.
echo Server stopped. Press any key to exit...
pause >nul
