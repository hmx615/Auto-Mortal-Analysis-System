@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Install Visualization Dependencies
echo ============================================================
echo.
echo Installing required packages:
echo   - pandas (Data processing)
echo   - plotly (Interactive charts)
echo   - numpy (Numerical computing)
echo   - scipy (Statistical analysis)
echo.
echo Using mirror: Tsinghua University (China)
echo.

pip install pandas plotly numpy scipy -i https://pypi.tuna.tsinghua.edu.cn/simple

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
echo   - pandas
echo   - plotly
echo   - numpy
echo   - scipy
echo.
echo Next step: Run visualize_mortal.py to generate report
echo.

pause
