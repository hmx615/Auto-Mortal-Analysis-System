@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Mortal AI Analysis Result Visualization
echo ============================================================
echo.
echo Generating interactive dashboard...
echo.

REM Default: filter out data with rating < 80
python visualize_mortal.py

REM Customize rating threshold (uncomment and modify as needed):
REM python visualize_mortal.py --min-rating 85
REM python visualize_mortal.py --min-rating 0

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed! Dependencies may be missing
    echo.
    echo Please run: install_requirements.bat
    echo.
    pause
    exit /b 1
)

echo.
echo Done! Browser should open automatically.
echo.
pause
