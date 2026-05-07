import ipaddress
import os
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from typing import Dict, List, Optional, Tuple

import paramiko


class NetworkScanner:
    def __init__(self, ssh_port: int = 22, timeout: float = 0.5, workers: int = 30, ssh_ports: Optional[List[int]] = None):
        self.ssh_port = ssh_port
        self.ssh_ports = sorted(set(ssh_ports or [ssh_port]))
        self.timeout = timeout
        self.workers = workers
        self._lock = threading.Lock()
        self.progress = 0
        self.total = 0

    def _resolve_local_ip(self) -> str:
        for endpoint in [("8.8.8.8", 80), ("1.1.1.1", 80)]:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(endpoint)
                ip = s.getsockname()[0]
                if ip and not ip.startswith("127."):
                    return ip
            except OSError:
                continue
            finally:
                s.close()

        hostname_ip = socket.gethostbyname(socket.gethostname())
        if hostname_ip and not hostname_ip.startswith("127."):
            return hostname_ip
        return "127.0.0.1"

    def _load_scan_cidrs(self) -> List[ipaddress.IPv4Network]:
        raw_cidrs = os.getenv("SCAN_CIDRS", "").strip()
        if raw_cidrs:
            networks: List[ipaddress.IPv4Network] = []
            for token in raw_cidrs.split(","):
                token = token.strip()
                if not token:
                    continue
                try:
                    networks.append(ipaddress.ip_network(token, strict=False))
                except ValueError:
                    continue
            if networks:
                return networks

        local_ip = self._resolve_local_ip()
        return [ipaddress.ip_network(f"{local_ip}/24", strict=False)]

    def _lan_scan_targets(self) -> List[Tuple[str, int]]:
        max_hosts_raw = os.getenv("SCAN_MAX_HOSTS", "1024").strip()
        max_hosts = int(max_hosts_raw) if max_hosts_raw.isdigit() else 1024
        hosts: List[str] = []
        for network in self._load_scan_cidrs():
            for ip in network.hosts():
                hosts.append(str(ip))
                if len(hosts) >= max_hosts:
                    break
            if len(hosts) >= max_hosts:
                break
        return list(product(sorted(set(hosts)), self.ssh_ports))

    def _port_open(self, host: str, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            return sock.connect_ex((host, port)) == 0
        except OSError:
            # Имя хоста может не резолвиться.
            return False
        finally:
            sock.close()

    def _docker_scan_targets(self) -> List[Tuple[str, int]]:
        # На хосте локальные адреса.
        # Имена сервисов задаём явно.
        # Внутри контейнерной сети.
        raw_hosts = os.getenv("DOCKER_SCAN_TARGETS", "127.0.0.1,localhost,host.docker.internal")
        hosts = [host.strip() for host in raw_hosts.split(",") if host.strip()]
        raw_ports = os.getenv("DOCKER_SSH_PORTS", "2222,2223,8022,22")
        ports: List[int] = []
        for token in raw_ports.split(","):
            token = token.strip()
            if token.isdigit():
                ports.append(int(token))
        if not ports:
            ports = self.ssh_ports
        return list(product(hosts, sorted(set(ports))))

    def scan_open_ssh_hosts(self) -> List[Dict[str, object]]:
        lan_targets = self._lan_scan_targets()
        docker_targets = self._docker_scan_targets()
        all_targets = list({(host, port) for host, port in (lan_targets + docker_targets)})
        self.total = len(all_targets)
        found: List[Dict[str, object]] = []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(self._port_open, host, port): (host, port) for host, port in all_targets}
            for fut in as_completed(futures):
                host, port = futures[fut]
                if fut.result():
                    source = "docker" if host in {"127.0.0.1", "localhost", "host.docker.internal", "raspberry", "ubuntu", "android"} else "lan"
                    found.append({"host": host, "port": port, "source": source})
                with self._lock:
                    self.progress += 1
        return sorted(found, key=lambda x: (str(x["host"]), int(x["port"])))

    def _credential_candidates(self, username: Optional[str], password: Optional[str]) -> List[Tuple[Optional[str], Optional[str]]]:
        candidates: List[Tuple[Optional[str], Optional[str]]] = []
        if username is not None or password is not None:
            candidates.append((username, password))
        candidates.extend(
            [
                ("pi", "raspberry"),
                ("root", "raspberry"),
                ("root", "root"),
                ("android", "android"),
            ]
        )

        # Сохраняем порядок без дублей.
        unique: List[Tuple[Optional[str], Optional[str]]] = []
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            unique.append(candidate)
        return unique

    def detect_device_type(
        self,
        host: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict:
        target_port = port or self.ssh_port
        result = {"ip": host, "host": host, "port": target_port, "type": "unknown"}
        docker_hosts = {"127.0.0.1", "localhost", "host.docker.internal", "raspberry", "ubuntu", "android"}
        if host in docker_hosts:
            # Быстрые подсказки типа устройства.
            if target_port == 2222:
                result.update({"type": "raspberry_pi", "username": "pi", "type_guess": True})
            elif target_port == 2223:
                result.update({"type": "linux", "username": "root", "type_guess": True})
            elif target_port == 8022:
                result.update({"type": "android", "username": "root", "type_guess": True})
        last_error = None

        for login, secret in self._credential_candidates(username, password):
            if not login:
                continue
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    hostname=host,
                    port=target_port,
                    username=login,
                    password=secret,
                    timeout=3,
                    allow_agent=False,
                    look_for_keys=False,
                )
                result["username"] = login
                for cmd, dtype, probe in [
                    ("cat /proc/device-tree/model", "raspberry_pi", "Raspberry Pi"),
                    ("devicefs-cat /proc/device-tree/model", "raspberry_pi", "Raspberry Pi"),
                    ("getprop ro.build.version.release", "android", ""),
                    ("uname -a", "linux", "Linux"),
                ]:
                    _, stdout, _ = client.exec_command(cmd, timeout=3)
                    out = stdout.read().decode("utf-8", errors="ignore").strip()
                    if (probe and probe in out) or (dtype == "android" and out):
                        result["type"] = dtype
                        result["probe_output"] = out
                        break
                if result["type"] == "unknown":
                    result["type"] = "linux"
                result.pop("type_guess", None)
                return result
            except paramiko.AuthenticationException:
                last_error = "authentication_failed"
                continue
            except Exception:
                last_error = "unreachable_or_ssh_error"
                continue
            finally:
                try:
                    client.close()
                except Exception:
                    pass
        if last_error:
            result["status"] = last_error
        return result
