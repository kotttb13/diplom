#!/bin/bash
set -euo pipefail

SSH_USER="${SSH_USER:-pi}"
SSH_PASSWORD="${SSH_PASSWORD:-raspberry}"

# Create user if missing
if ! id -u "$SSH_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$SSH_USER"
  usermod -aG sudo "$SSH_USER" || true
fi

echo "${SSH_USER}:${SSH_PASSWORD}" | chpasswd
echo "root:${SSH_PASSWORD}" | chpasswd

# Host keys
ssh-keygen -A

# Optional: present a Raspberry-like model file snapshot under /_device
mkdir -p /_device/proc/device-tree || true

# Helper to view "device-like" proc/sys snapshots
cat >/usr/local/bin/devicefs-cat <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: devicefs-cat /proc/cpuinfo|/proc/meminfo|/sys/.../scaling_cur_freq|/proc/device-tree/model" >&2
  exit 2
fi
req="$1"
mapped="/_device${req}"
if [[ -f "$mapped" ]]; then
  cat "$mapped"
  exit 0
fi
echo "No snapshot for $req at $mapped" >&2
exit 1
EOF
chmod +x /usr/local/bin/devicefs-cat

exec /usr/sbin/sshd -D -e

