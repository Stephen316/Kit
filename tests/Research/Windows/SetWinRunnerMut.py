import json as JsonCodec
import sys as System

from tests.Research.SupervisorClient import SessionHost


def SetWinRunnerMut(Harness: SessionHost, MemoryLimit: int = 512) -> None:
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
