import json as JsonCodec
import sys as System

from tests.Research.SupervisorClient import SessionHost


# windows custody coverage requires a job aware runner registered with the actual supervisor
def SetWinRunner(Harness: SessionHost, MemoryLimit: int = 512) -> None:
    ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    ConfigInfo["adaptive_limits"] = True
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    RegistryFile = Harness.RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    for EntryInfo in Registry["runners"].values():
        EntryInfo["argv"] = [
            System.executable,
            "-m",
            "tests.Research.Windows.WindowsRunner",
            "{session}",
        ]
        EntryInfo["initial_peak_memory_mib"] = 64
        EntryInfo["max_memory_mib"] = MemoryLimit
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
