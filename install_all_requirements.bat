@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Install ALL Dependencies for Mortal Analysis System
echo ============================================================
echo.
echo This will install dependencies for:
echo   - Crawler module
echo   - Analysis module
echo   - Visualization module
echo   - Auto update module
echo.
echo Total packages to install:
echo   - requests (HTTP library)
echo   - selenium (Browser automation)
echo   - webdriver-manager (WebDriver management)
echo   - pandas (Data processing)
echo   - plotly (Interactive charts)
echo   - numpy (Numerical computing)
echo   - matplotlib (Plotting)
echo   - scipy (Statistical analysis)
echo   - 2captcha-python (CAPTCHA solving)
echo.
echo Using mirror: Tsinghua University (China)
echo.
pause
echo.
echo Installing all packages...
echo.

pip install requests selenium webdriver-manager pandas plotly numpy matplotlib scipy 2captcha-python -i https://pypi.tuna.tsinghua.edu.cn/simple

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
echo All modules are ready to use:
echo   [OK] Crawler module
echo   [OK] Analysis module
echo   [OK] Visualization module
echo   [OK] Auto update module
echo.
echo Installed packages:
echo   - requests
echo   - selenium
echo   - webdriver-manager
echo   - pandas
echo   - plotly
echo   - numpy
echo   - matplotlib
echo   - scipy
echo   - 2captcha-python
echo.
echo Next steps:
echo   1. Configure player IDs in crawler module (crawler folder)
echo   2. Run crawler: Open crawler folder, run run_crawl.bat
echo   3. Run analysis: Open analysis folder, run run_all_headless.bat
echo   4. Generate report: Open visualization folder, run run_visualization.bat
echo.

pause
