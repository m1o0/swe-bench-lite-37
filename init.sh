#!/usr/bin/env bash
# WSL 初始化:启用 systemd + 创建用户
set -e
printf '[boot]\nsystemd=true\n' > /etc/wsl.conf
id -u mio >/dev/null 2>&1 || useradd -m -G sudo mio
echo 'mio ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/mio
chmod 440 /etc/sudoers.d/mio
echo INIT_OK
