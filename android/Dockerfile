FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_INDEX_URL

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    ca-certificates \
    python3 python3-pip python3-numpy \
    bash \
    iproute2 net-tools procps netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd

# Install onnxruntime via pip. In restricted networks you MUST provide a reachable mirror via PIP_INDEX_URL.
# We try a mirror list; if all fail, we keep the container usable for SSH tests (Python is still present).
RUN set -e; \
    if [ -n "${PIP_INDEX_URL:-}" ]; then CANDIDATES="$PIP_INDEX_URL"; \
    else CANDIDATES="https://pypi.tuna.tsinghua.edu.cn/simple https://pypi.org/simple"; fi; \
    OK=0; \
    for IDX in $CANDIDATES; do \
      echo "Trying pip index: $IDX"; \
      python3 -m pip install --no-cache-dir --break-system-packages --timeout 120 --retries 10 onnxruntime -i "$IDX" && OK=1 && break || true; \
    done; \
    if [ "$OK" -eq 1 ]; then python3 -c "import onnxruntime as ort; print('onnxruntime', ort.__version__)"; \
    else echo "WARNING: onnxruntime not installed (set PIP_INDEX_URL to a reachable PyPI mirror)"; fi

# Configure SSH to listen on 8022 (Termux-like)
RUN sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication yes/g' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin yes/g' /etc/ssh/sshd_config && \
    echo "Port 8022" >> /etc/ssh/sshd_config && \
    echo "ListenAddress 0.0.0.0" >> /etc/ssh/sshd_config

# Android/Termux-like helpers (very small; SSH/Python are real)
RUN mkdir -p /data/data/com.termux/files/home && \
    printf '%s\n' '#!/usr/bin/env bash' \
      'if [ "$1" = "ro.build.version.release" ]; then echo "11"; exit 0; fi' \
      'if [ "$1" = "ro.product.cpu.abi" ]; then uname -m; exit 0; fi' \
      'exit 0' \
      > /usr/local/bin/getprop && chmod +x /usr/local/bin/getprop

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8022

ENTRYPOINT ["/entrypoint.sh"]