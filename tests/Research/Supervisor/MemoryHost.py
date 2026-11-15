import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


def MakeMemoryHost(RootPath: FilePath) -> SessionHost:
    Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    RunnerInfo = Registry["runners"]["fixture.decode"]
    RunnerInfo["argv"] = [
        System.executable,
        str(FilePath(__file__).with_name("MemoryRunner.py")),
        "{session}",
    ]
    RunnerInfo["initial_peak_memory_mib"] = 16
    RunnerInfo["max_memory_mib"] = 64
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    return Harness
