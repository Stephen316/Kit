import os
import re
import subprocess
import sys
from pathlib import Path


def command_output(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False, env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"})
    except (OSError, subprocess.SubprocessError) as error:
        raise OSError("required resource measurement unavailable") from error
    if result.returncode != 0:
        raise OSError("required resource measurement failed")
    return result.stdout


def host_resources():
    cpus = os.cpu_count()
    if cpus is None or cpus < 1:
        raise OSError("logical CPU count unavailable")
    if hasattr(os, "sched_getaffinity"):
        cpus = min(cpus, len(os.sched_getaffinity(0)))
    if sys.platform.startswith("linux"):
        content = Path("/proc/meminfo").read_text(encoding="ascii")
        matched = re.search(r"^MemAvailable:\s+(\d+)\s+kB$", content, re.MULTILINE)
        if matched is None:
            raise OSError("MemAvailable measurement unavailable")
        memory = int(matched[1]) * 1024
        source = "linux:MemAvailable"
    elif sys.platform == "darwin":
        content = command_output(["/usr/bin/vm_stat"])
        matched = re.search(r"page size of (\d+) bytes", content)
        pages = dict(re.findall(r"^(Pages free|Pages inactive|Pages purgeable):\s+(\d+)\.", content, re.MULTILINE))
        if matched is None or len(pages) != 3:
            raise OSError("vm_stat memory measurement unavailable")
        memory = (int(pages["Pages free"]) + max(int(pages["Pages inactive"]), int(pages["Pages purgeable"]))) * int(matched[1])
        source = "macos:vm_stat:free+max(inactive,purgeable)"
    else:
        raise OSError("resource measurement requires Linux or macOS")
    return {"logical_cpus": cpus, "available_memory_bytes": memory, "memory_source": source}


def group_memory(pids):
    if not pids:
        return {}
    content = command_output(["/bin/ps", "-axo", "pid=,pgid=,rss=,stat="])
    groups = {}
    for line in content.splitlines():
        fields = line.split()
        if len(fields) != 4 or not all(value.isdigit() for value in fields[:3]):
            raise OSError("invalid process group memory measurement")
        group = int(fields[1])
        if group in pids:
            groups.setdefault(group, 0)
            if not fields[3].startswith("Z"):
                groups[group] += int(fields[2]) * 1024
    return groups
