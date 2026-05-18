import re
import os
import time
from datetime import datetime
from typing import Dict, Optional

from .linux_device_manager import LinuxDeviceManager


class RaspberryPiManager(LinuxDeviceManager):
    def _read_snapshot(self, path: str) -> str:
        result = self.execute_command(f"devicefs-cat {path}", timeout=8)
        if result.get("success"):
            return (result.get("output") or "").strip()

        mapped = f"/_device{path}"
        fallback = self.execute_command(f"cat {mapped}", timeout=8)
        if fallback.get("success"):
            return (fallback.get("output") or "").strip()
        return ""

    def _parse_cpu_cores(self, cpuinfo: str) -> int:
        if not cpuinfo:
            return 4
        cores = len(re.findall(r"^processor\s*:\s*\d+", cpuinfo, flags=re.MULTILINE))
        parsed = cores if cores > 0 else 4
        return min(parsed, 4)

    def _parse_memtotal_gb(self, meminfo: str) -> int:
        if not meminfo:
            return 4
        match = re.search(r"MemTotal:\s*([0-9]+)\s*kB", meminfo)
        if not match:
            return 4
        mem_kb = int(match.group(1))
        mem_gb = max(1, int(round(mem_kb / 1024 / 1024)))
        detected = min([1, 2, 4, 8], key=lambda x: abs(x - mem_gb))
        return min(detected, 4)

    def _parse_cpu_frequency_mhz(self) -> int:
        clock = self.execute_command("vcgencmd measure_clock arm", timeout=8)
        if clock.get("success"):
            match = re.search(r"frequency\(48\)=([0-9]+)", clock.get("output", ""))
            if match:
                return min(int(int(match.group(1)) / 1_000_000), 1500)

        snapshot_freq = self._read_snapshot("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
        if snapshot_freq.isdigit():
            return min(int(int(snapshot_freq) / 1000), 1500)
        return 1500

    def _parse_gpu_memory_mb(self) -> int:
        gpu_mem = self.execute_command("vcgencmd get_mem gpu", timeout=8)
        if gpu_mem.get("success"):
            match = re.search(r"gpu=([0-9]+)M", gpu_mem.get("output", ""))
            if match:
                return min(int(match.group(1)), 256)
        return 256

    def _parse_storage_gb(self) -> int:
        sim_storage = os.getenv("RPI_SIM_STORAGE_GB", "4").strip()
        default_gb = int(sim_storage) if sim_storage.isdigit() else 4

        storage_cmd = self.execute_command(
            "df -BG / | awk 'NR==2{gsub(/G/,\"\",$4); print $4}'",
            timeout=8,
        )
        if storage_cmd.get("success") and str(storage_cmd.get("output", "")).strip().isdigit():
            storage_gb = int(str(storage_cmd.get("output")).strip())
            if storage_gb > 16:
                return default_gb
            return min(storage_gb, 4)
        return default_gb

    def get_device_info(self) -> Dict:
        cpuinfo = self._read_snapshot("/proc/cpuinfo")
        meminfo = self._read_snapshot("/proc/meminfo")
        model_text = self._read_snapshot("/proc/device-tree/model") or "Raspberry Pi 4 Model B Rev 1.4"

        info = {
            "last_seen": datetime.now(),
            "type_device": "raspberry_pi",
            "ip_address": self.ip,
            "architecture": "aarch64",
            "memory_gb": self._parse_storage_gb(),
            "ram_gb": self._parse_memtotal_gb(meminfo),
            "cpu_core": self._parse_cpu_cores(cpuinfo),
            "cpu_frequency": self._parse_cpu_frequency_mhz(),
            "gpu_memory": self._parse_gpu_memory_mb(),
            "board_model": model_text,
        }

        if not cpuinfo and not meminfo:
            linux_info = super().get_device_info()
            for key in ("architecture", "memory_gb", "ram_gb", "cpu_core", "cpu_frequency", "gpu_memory"):
                value = linux_info.get(key)
                if value not in (None, "", "Не доступно: Unknown error"):
                    info[key] = value
            info["type_device"] = "raspberry_pi"

        return info

    def get_system_info(self) -> Dict:
        info = self.get_device_info()
        info["type_device"] = "raspberry_pi"

        clock = self.execute_command("vcgencmd measure_clock arm", timeout=8)
        model = self.execute_command("cat /proc/device-tree/model", timeout=8)
        gpu_mem = self.execute_command("vcgencmd get_mem gpu", timeout=8)

        if clock.get("success"):
            m = re.search(r"frequency\(48\)=([0-9]+)", clock.get("output", ""))
            if m:
                info["cpu_frequency"] = int(int(m.group(1)) / 1_000_000)

        if model.get("success"):
            info["architecture"] = model.get("output", "").strip() or info.get("architecture")

        if gpu_mem.get("success"):
            m = re.search(r"gpu=([0-9]+)M", gpu_mem.get("output", ""))
            info["gpu_memory"] = int(m.group(1)) if m else None

        return info

    def install_dependencies(self) -> Dict:
        commands = [
            "sudo apt-get update -y",
            "sudo apt-get install -y python3 python3-pip",
            "python3 -m pip install --upgrade pip",
            "python3 -m pip install numpy onnxruntime tflite-runtime",
        ]
        results = [self.execute_command(cmd, timeout=120) for cmd in commands]
        failed = [r for r in results if not r.get("success")]
        return {"success": not failed, "results": results}
