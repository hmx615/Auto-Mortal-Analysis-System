@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python cheat_check/cheat_detector.py %*
pause
