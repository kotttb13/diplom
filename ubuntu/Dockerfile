FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_INDEX_URL

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    ca-certificates \
    python3 python3-pip python3-numpy \
    iproute2 net-tools procps netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd

RUN sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication yes/g' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Install onnxruntime via pip (try mirror if pypi.org is blocked).
RUN set -e; \
    if [ -n "${PIP_INDEX_URL:-}" ]; then CANDIDATES="$PIP_INDEX_URL"; \
    else CANDIDATES="https://pypi.tuna.tsinghua.edu.cn/simple https://pypi.org/simple"; fi; \
    for IDX in $CANDIDATES; do \
      echo "Trying pip index: $IDX"; \
      python3 -m pip install --no-cache-dir --timeout 120 --retries 10 onnxruntime -i "$IDX" && break; \
    done; \
    python3 -c "import onnxruntime as ort; print('onnxruntime', ort.__version__)"

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]