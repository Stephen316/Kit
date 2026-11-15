import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


def SetOutputRunner(Harness: SessionHost) -> None:
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    RegistryPath = FilePath(Config["registry"])
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    for Entry in Registry["runners"].values():
        Entry["argv"] = [
            System.executable,
            str(FilePath(__file__).with_name("OutputRunner.py")),
            "{session}",
        ]
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
