import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot, SessionHost


# supervisor coverage needs to dispatch through the real application registry for the selected installation
def SetAppRunner(Harness: SessionHost, ConfigFile: FilePath) -> None:
    RegistryFile = Harness.RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    Registry["runners"]["fixture.app"]["argv"] = [
        System.executable,
        str(KRepoRoot / "re/automation/ApplicationWorkers/FusionApplicationWorker.py"),
        "--installation",
        str(ConfigFile),
        "{session}",
    ]
    Registry["runners"]["fixture.app"]["result_schema"] = str(
        KRepoRoot / "re/automation/ApplicationWorkers/ApplicationResult.json"
    )
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    Config["resources"] = {"application:missing": 1}
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    Result = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:missing",
            "--capacity",
            "1",
            "--available",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stderr
