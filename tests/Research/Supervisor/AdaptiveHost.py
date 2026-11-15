import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


def MakeAdaptive(RootPath: FilePath, PoolLimit: int = 2) -> SessionHost:
    Harness = SessionHost(RootPath, {"decode": PoolLimit}, {"fixture.decode": "decode"})
    ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    del ConfigInfo["adaptive_limits"]
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    RunnerInfo = Registry["runners"]["fixture.decode"]
    RunnerInfo["argv"] = [
        System.executable,
        str(FilePath(__file__).with_name("AdaptiveRunner.py")),
        "{session}",
    ]
    RunnerInfo["initial_peak_memory_mib"] = 128
    RunnerInfo["max_memory_mib"] = 256
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    return Harness
