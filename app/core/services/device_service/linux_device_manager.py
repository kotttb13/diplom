import logging
import socket
import time
from typing import Dict

import paramiko

from .base_device_manager import BaseDeviceManager


class LinuxDeviceManager(BaseDeviceManager):
    def __init__(self):
        self.ip = None
        self.connection = None
        self.logger = logging.getLogger(__name__)

    def connect(self, host: str, username: str, password: str, port: int = 22) -> bool:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ip = host
            client.connect(
                hostname=host,
                username=username,
                password=password,
                port=port,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
            self.connection = client
            return True
        except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout):
            return False
        except Exception:
            return False

    def execute_command(self, command: str, timeout: int = 30) -> Dict:
        if not self.connection:
            return {"success": False, "error": "Нет подключения"}
        try:
            _, stdout, stderr = self.connection.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            return {
                "success": exit_status == 0,
                "exit_status": exit_status,
                "output": stdout.read().decode("utf-8", errors="ignore").strip(),
                "error": stderr.read().decode("utf-8", errors="ignore").strip(),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_device_info(self) -> Dict:
        info = {"last_seen": time.strftime("%Y-%m-%d %H:%M:%S"), "type_device": "linux", "ip_address": self.ip}
        commands = {
            "architecture": "uname -m",
            "memory_gb": "df -h / | awk 'NR==2{print $4}' | sed 's/G//'",
            "ram_gb": "awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo",
            "cpu_core": "nproc",
            "cpu_frequency": "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null",
        }
        for key, command in commands.items():
            result = self.execute_command(command)
            value = result.get("output", "") if result.get("success") else ""
            if key == "cpu_frequency" and value:
                try:
                    info[key] = int(float(value) / 1000.0)
                except Exception:
                    info[key] = None
            else:
                info[key] = value or None
        info["gpu_memory"] = None
        return info

    def get_free_memory(self) -> Dict:
        return self.execute_command("df -h / | awk 'NR==2{print $4}' | sed 's/G//'")

    def deploy_file(self, local_path: str, remote_path: str = "~/") -> Dict:
        if not self.connection:
            return {"success": False, "error": "Нет SSH подключения"}
        try:
            remote_path_fixed = remote_path
            if remote_path.startswith("~/"):
                home_result = self.execute_command("echo $HOME")
                if home_result.get("success") and home_result.get("output"):
                    remote_path_fixed = remote_path.replace("~/", f"{home_result.get('output').strip()}/")
            remote_dir = remote_path_fixed.rsplit("/", 1)[0] if "/" in remote_path_fixed else ""
            if remote_dir:
                self.execute_command(f'mkdir -p "{remote_dir}"')
            with self.connection.open_sftp() as sftp:
                sftp.put(local_path, remote_path_fixed)
            return {"success": True, "remote_path": remote_path, "actual_path": remote_path_fixed}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
