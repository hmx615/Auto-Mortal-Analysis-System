@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Install Auto Update Dependencies
echo ============================================================
echo.
echo Note: Auto update requires dependencies from both:
echo   - Crawler module (requests, selenium)
echo   - Analysis module (selenium, webdriver-manager, requests, pandas, 2captcha-python, numpy, matplotlib, scipy)
echo.
echo Installing all required packages...
echo.
echo Using mirror: Tsinghua University (China)
echo.

pip install requests selenium webdriver-manager pandas 2captcha-python numpy matplotlib scipy -i https://pypi.tuna.tsinghua.edu.cn/simple

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
echo   - webdriver-manager
echo   - pandas
echo   - 2captcha-python
echo   - numpy
echo   - matplotlib
echo   - scipy
echo.
echo Next step: Run auto_update.py or use run_auto_update.bat
echo.

pause
