@echo off
title Directory Analytics CLI Tool
echo.
echo  ============================================================
echo    DIRECTORY ANALYTICS CLI TOOL
echo  ============================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.6+ and try again.
    echo.
    pause
    exit /b 1
)

:: Run the main Python script
python dir_analytics.py

:: Keep window open on error
if %ERRORLEVEL% neq 0 (
    echo.
    echo  [ERROR] Script exited with error code %ERRORLEVEL%
    pause
)
