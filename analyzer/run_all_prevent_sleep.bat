@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Run ALL Records in HEADLESS Mode - Prevent Sleep
echo ============================================================
echo.
echo HEADLESS mode: Browser runs in background - no window
echo PREVENT SLEEP: Using PowerCfg to prevent system sleep
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
echo You can lock your account or turn off monitor safely!
echo The system will stay awake until analysis completes.
echo.
pause
echo.
echo Preventing system sleep...
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
echo.
echo Starting analysis...
echo.

python win_mortal_analyzer_2captcha.py --limit 99999 --headless

echo.
echo ============================================================
echo Complete!
echo ============================================================
echo.
echo Restoring original sleep settings...
echo Please manually restore your preferred sleep timeout if needed.
echo Go to: Settings ^> System ^> Power ^& sleep
echo.
pause
