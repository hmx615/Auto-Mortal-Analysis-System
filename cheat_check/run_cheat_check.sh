#!/bin/bash
cd "$(dirname "$0")/.."
~/miniconda3/bin/python cheat_check/cheat_detector.py "$@"
echo ""
read -p "按回车退出..." _
