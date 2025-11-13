@echo off
title Career Assessment System
echo.
echo ========================================
echo    CAREER ASSESSMENT SYSTEM LAUNCHER
echo ========================================
echo.
echo Starting the Career Assessment Server...
echo.

cd /d "%~dp0"
python start_server.py

pause
