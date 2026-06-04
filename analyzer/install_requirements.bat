@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Install Analysis Dependencies
echo ============================================================
echo.
echo Installing required packages:
echo   - selenium (Browser automation)
echo   - webdriver-manager (WebDriver management)
echo   - requests (HTTP library)
echo   - pandas (Data processing)
echo   - 2captcha-python (CAPTCHA solving)
echo   - numpy (Numerical computing)
echo   - matplotlib (Plotting)
echo   - scipy (Scientific computing)
echo.
echo Using mirror: Tsinghua University (China)
echo.

pip install selenium webdriver-manager requests pandas 2captcha-python numpy matplotlib scipy -i https://pypi.tuna.tsinghua.edu.cn/simple

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
echo   - selenium
echo   - webdriver-manager
echo   - requests
echo   - pandas
echo   - 2captcha-python
echo   - numpy
echo   - matplotlib
echo   - scipy
echo.
echo Next step: Run win_mortal_analyzer_2captcha.py to start analysis
echo.

pause
