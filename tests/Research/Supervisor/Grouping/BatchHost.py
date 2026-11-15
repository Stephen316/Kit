import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot, SessionHost


# grouped sessions need the real controller to check independent leases and artifact ownership
def MakeBatchHost(RootPath: FilePath) -> SessionHost:
    StorePath = RootPath / "Store"
    ResultInfo = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(StorePath),
            "init",
            "--max-running",
            "64",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    Harness = SessionHost(
        RootPath,
        {"decode": 1},
        {"fixture.decode": "decode"},
        {"adapter": "a03", "store": str(StorePath)},
    )
    Harness.StorePath = StorePath
    WriteBatchReg(RootPath)
    Harness.BindBytes("source", b"synthetic process fixture")
    return Harness


# grouped process cases need a worker with declared memory estimates and protocol support
def WriteBatchReg(RootPath: FilePath) -> None:
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    RunnerInfo = Registry["runners"]["fixture.decode"]
    RunnerInfo.update(
        {
            "argv": [
                System.executable,
                str(FilePath(__file__).with_name("BatchRunner.py")),
                "{session}",
            ],
            "initial_peak_memory_mib": 32,
            "max_memory_mib": 256,
            "group_protocol": 1,
            "group_peak_memory_mib": 64,
        }
    )
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
