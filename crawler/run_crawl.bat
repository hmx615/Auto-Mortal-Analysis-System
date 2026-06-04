@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo Crawl All Paipu from API
echo ============================================================
echo.
echo Getting ALL records from API (no limit)
echo.
echo Output: ../data/paipu_list.csv
echo.

python crawl_all.py 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Script failed with error code %errorlevel%
    echo Please check the error messages above
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo Complete!
echo ============================================================
echo.
timeout /t 3 /nobreak >nul
