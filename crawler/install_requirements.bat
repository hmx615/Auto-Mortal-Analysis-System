@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Install Crawler Dependencies
echo ============================================================
echo.
echo Installing required packages:
echo   - requests (HTTP library)
echo   - selenium (Browser automation)
echo.
echo Using mirror: Tsinghua University (China)
echo.

pip install requests selenium -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Installation failed!
    echo ============================================================
    echo.
    echo Possible reasons:
    echo   - Python not installed or not in PATH
    echo   - Network connection issues
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Installed packages:
echo   - requests
echo   - selenium
echo.
echo Next step: Run crawl_all.py to start crawling
echo.

pause
