from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
import psutil

ROOT = Path(__file__).resolve().parents[1]


def read_optional(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def actual_environment():
    cpu = platform.processor()
    cpuinfo = read_optional("/proc/cpuinfo")
    if cpuinfo:
        cpu = next((line.split(":", 1)[1].strip() for line in cpuinfo.splitlines() if line.startswith("model name")), cpu)
    env = {"os": platform.platform(), "python": sys.version, "executable": sys.executable,
           "cpu": cpu, "logical_cpu": os.cpu_count(), "ram_total_bytes": psutil.virtual_memory().total,
           "ram_available_bytes": psutil.virtual_memory().available,
           "cgroup_memory_max": read_optional("/sys/fs/cgroup/memory.max"),
           "cgroup_cpu_max": read_optional("/sys/fs/cgroup/cpu.max"),
           "accessible_usb_serial": [str(p) for pattern in ("ttyUSB*", "ttyACM*") for p in Path("/dev").glob(pattern)],
           "nvidia_devices": [str(p) for p in Path("/dev").glob("nvidia*")],
           "bluetooth_interfaces": [str(p) for p in Path("/sys/class/bluetooth").glob("*")],
           "cwd": str(Path.cwd()), "file_read_write_test": "프로젝트 디렉터리 파일 생성/읽기 확인",
           "target_pc_measured": False, "hardware_measured": False}
    env["environment_id"] = hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()[:20]
    return env


def source_version():
    digest = hashlib.sha256()
    for pattern in ("**/*.py", "configs/*.yaml", "requirements*.txt", "models/quality.json"):
        for file in sorted(ROOT.glob(pattern)):
            if "__pycache__" in str(file):
                continue
            digest.update(str(file.relative_to(ROOT)).encode())
            digest.update(file.read_bytes())
    return "sha256:" + digest.hexdigest()


class MemorySampler:
    def __init__(self):
        self.process = psutil.Process()
        self.peak = self.process.memory_info().rss
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.wait(.02):
            self.peak = max(self.peak, self.process.memory_info().rss)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.peak = max(self.peak, self.process.memory_info().rss)
        self.stop.set()
        self.thread.join()
