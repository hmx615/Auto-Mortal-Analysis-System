@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Run ALL Records in HEADLESS Mode - Background
echo ============================================================
echo.
echo HEADLESS mode: Browser runs in background - no window
echo.
if defined TWOCAPTCHA_API_KEY (
    echo API Key: Using environment variable TWOCAPTCHA_API_KEY
) else (
    echo API Key: Not configured - will use manual mode
    echo To configure: set TWOCAPTCHA_API_KEY=YOUR_API_KEY
)
echo.
echo This will process ALL records in paipu_list.csv
echo Auto-skip already analyzed records - deduplication enabled
echo.
echo You can continue using your computer normally!
echo The browser will run in the background.
echo.
pause

python win_mortal_analyzer_2captcha.py --limit 99999 --headless

echo.
echo ============================================================
echo Complete!
echo ============================================================
echo.
