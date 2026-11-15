import math
import os
import re
import sys
from pathlib import Path


def adaptive_metrics():
    load, pressure = None, None
    try:
        measured = os.getloadavg()[0]
        if math.isfinite(measured) and measured >= 0:
            load = measured
    except (AttributeError, OSError):
        pass
    if sys.platform.startswith("linux"):
        try:
            content = Path("/proc/pressure/memory").read_text(encoding="ascii")
            matched = re.search(r"^some avg10=([0-9]+(?:\.[0-9]+)?)\s", content, re.MULTILINE)
            if matched is not None and 0 <= float(matched[1]) <= 100:
                pressure = float(matched[1])
        except (OSError, UnicodeDecodeError):
            pass
    return {"load_average_1m": load, "memory_some_avg10": pressure, "memory_pressure_required": sys.platform.startswith("linux")}
