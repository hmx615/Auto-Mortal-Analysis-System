#!/bin/bash
cd "$(dirname "$0")"
~/miniconda3/bin/python run_analysis.py "$@"
echo "按回车退出"
read
