#!/bin/bash
set -euo pipefail

SSH_USER="${SSH_USER:-root}"
SSH_PASSWORD="${SSH_PASSWORD:-raspberry}"

if [[ "$SSH_USER" != "root" ]] && ! id -u "$SSH_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$SSH_USER"
fi

echo "root:${SSH_PASSWORD}" | chpasswd
if [[ "$SSH_USER" != "root" ]]; then
  echo "${SSH_USER}:${SSH_PASSWORD}" | chpasswd
fi

ssh-keygen -A

cat >/usr/local/bin/devicefs-cat <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: devicefs-cat /proc/cpuinfo|/proc/meminfo|/sys/.../scaling_cur_freq" >&2
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

