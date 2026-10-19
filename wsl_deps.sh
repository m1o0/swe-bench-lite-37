#!/usr/bin/env bash
# WSL 测试依赖安装
set -e
python3 -m pip install -q pytz sqlparse asgiref -i https://mirrors.aliyun.com/pypi/simple/
python3 -c "import pytz, sqlparse, asgiref; print('DEPS_OK')"
