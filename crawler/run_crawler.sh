#!/bin/bash
cd "$(dirname "$0")"
~/miniconda3/bin/python crawl_all.py
echo "完成，按回车退出"
read
