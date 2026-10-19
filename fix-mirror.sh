#!/usr/bin/env bash
set -e
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run"
  ]
}
EOF
systemctl restart docker
sleep 2
docker info 2>/dev/null | grep -A3 -i "registry mirrors" || true
docker pull hello-world >/dev/null 2>&1 && echo "TRANSPARENT_MIRROR_OK"
