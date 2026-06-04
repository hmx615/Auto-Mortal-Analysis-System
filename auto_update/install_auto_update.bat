@echo off
chcp 65001 >nul

REM Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo Administrator Privileges Required!
    echo ============================================================
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo ============================================================
echo Install Auto Update - Background Service
echo ============================================================
echo.
echo This will install auto update as a background service:
echo   - Auto start on system boot
echo   - Run in background - no window
echo   - Keep running even if you log out
echo.

REM Ask user for update interval
echo Please select update interval:
echo   1. Every 6 hours - recommended
echo   2. Every 12 hours - default
echo   3. Every 24 hours - daily
echo   4. Custom interval - enter minutes
echo.
set /p CHOICE="Enter your choice (1-4): "

if "%CHOICE%"=="1" (
    set INTERVAL=360
    set INTERVAL_DESC=6 hours
) else if "%CHOICE%"=="2" (
    set INTERVAL=720
    set INTERVAL_DESC=12 hours
) else if "%CHOICE%"=="3" (
    set INTERVAL=1440
    set INTERVAL_DESC=24 hours
) else if "%CHOICE%"=="4" (
    set /p INTERVAL="Enter interval in minutes: "
    set INTERVAL_DESC=%INTERVAL% minutes
) else (
    echo Invalid choice. Using default: 12 hours
    set INTERVAL=720
    set INTERVAL_DESC=12 hours
)

echo.
echo Selected interval: %INTERVAL_DESC%
echo.

REM Find Python installation - get full path
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i
if not defined PYTHON_PATH (
    echo ============================================================
    echo Python Not Found!
    echo ============================================================
    echo.
    echo python command not found in PATH
    pause
    exit /b 1
)

echo Python found at: %PYTHON_PATH%

REM Update auto_update.py with selected interval
set CURRENT_DIR=%~dp0
set PYTHON_SCRIPT=%CURRENT_DIR%auto_update.py

echo Updating configuration...
powershell -Command "(Get-Content '%PYTHON_SCRIPT%') -replace 'UPDATE_INTERVAL_MINUTES = \d+', 'UPDATE_INTERVAL_MINUTES = %INTERVAL%' | Set-Content '%PYTHON_SCRIPT%'"

echo Creating scheduled task...

REM Delete old task if exists
schtasks /Delete /TN "MortalAutoUpdate" /F >nul 2>&1

REM Create new task - on system startup
REM Create batch wrapper to set working directory
set WRAPPER_BAT=%CURRENT_DIR%run_wrapper.bat

REM Create wrapper batch file
echo @echo off > "%WRAPPER_BAT%"
echo cd /d "%CURRENT_DIR%" >> "%WRAPPER_BAT%"
echo start /B "" "%PYTHON_PATH%" "%PYTHON_SCRIPT%" >> "%WRAPPER_BAT%"

REM Create VBS to run batch file hidden
set VBS_SCRIPT=%CURRENT_DIR%run_hidden.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo WshShell.Run """%WRAPPER_BAT%""", 0, False >> "%VBS_SCRIPT%"

schtasks /Create /TN "MortalAutoUpdate" /TR "wscript.exe //nologo \"%VBS_SCRIPT%\"" /SC ONSTART /RU SYSTEM /RL HIGHEST /F >nul

REM Verify task was created
schtasks /Query /TN "MortalAutoUpdate" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo Installation Failed!
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation Success!
echo ============================================================
echo.
echo Task name: MortalAutoUpdate
echo Trigger: On system boot
echo Update interval: %INTERVAL_DESC%
echo Log file: %CURRENT_DIR%auto_update.log
echo.
echo The service will start after next reboot
echo Or manually start: run_auto_update_silent.bat
echo.
echo To uninstall: Open Task Scheduler and delete MortalAutoUpdate
echo.

pause
