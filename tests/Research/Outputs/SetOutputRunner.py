import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


# output integration checks need a registered worker that can exercise artifact intake
def SetOutputRunner(Harness: SessionHost, KindName: str | None = None) -> None:
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    RegistryPath = FilePath(Config["registry"])
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    for RunnerKind, Entry in Registry["runners"].items():
        if KindName is not None and RunnerKind != KindName:
            continue
        Entry["argv"] = [
            System.executable,
            "-m",
            "tests.Research.Outputs.OutputRunner",
            "{session}",
        ]
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
