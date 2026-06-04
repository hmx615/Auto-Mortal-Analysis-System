@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Mortal 并行分析
echo ============================================================
echo.
echo 用法: 直接运行使用 config.py 中的 WORKER_COUNT
echo       或拖入数字参数指定 worker 数量
echo.
pause

python run_analysis.py %1

echo.
pause
