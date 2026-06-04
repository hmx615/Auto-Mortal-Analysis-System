@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Auto Update System - Manual Start
echo ============================================================
echo.
echo Function: Auto crawl and analyze new paipu every 30 minutes
echo.
echo Running mode:
echo   - Background headless browser
echo   - Auto deduplication (only new paipu)
echo   - Can minimize this window
echo.
echo Log file: auto_update.log
echo.
echo Press Ctrl+C to stop anytime
echo.
pause
echo.
echo Starting auto update system...
echo.

python auto_update.py

echo.
echo ============================================================
echo Auto Update System Stopped
echo ============================================================
echo.
pause
