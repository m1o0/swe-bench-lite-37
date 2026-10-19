#!/usr/bin/env bash
# SWE-bench 冲刺实验环境(Ubuntu 22.04,以 root 运行)
# 用法: bash <EXP_ROOT_POSIX>/setup.sh
set -e
export DEBIAN_FRONTEND=noninteractive
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "=== [1/4] Docker CE ==="
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
docker --version

echo "=== [2/4] Python venv ==="
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip >/dev/null
python3 -m venv /opt/ars

echo "=== [3/4] mini-swe-agent ==="
/opt/ars/bin/pip install -q -U pip -i "$MIRROR"
/opt/ars/bin/pip install -q -U mini-swe-agent -i "$MIRROR"

echo "=== [4/4] GLM 端点配置 ==="
if [ -n "$GLM_KEY" ]; then KEYVAL="$GLM_KEY"; else KEYVAL="填这里"; fi
cat > /opt/ars/glmenv <<EOF
export OPENAI_API_KEY=$KEYVAL
export OPENAI_API_BASE=https://api.z.ai/api/coding/paas/v4
EOF

echo "=== 验证 ==="
/opt/ars/bin/mini --help 2>&1 | head -15 || /opt/ars/bin/mini-swe-agent --help 2>&1 | head -15
echo SETUP_DONE
