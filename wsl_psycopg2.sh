#!/usr/bin/env bash
set -e
python3 -m pip install -q psycopg2-binary -i https://mirrors.aliyun.com/pypi/simple/
python3 -c "import psycopg2; print('PSYCOPG2_OK')"
