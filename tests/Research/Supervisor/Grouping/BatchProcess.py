import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot


def WaitBatchFlag(FlagFile: FilePath, Running: Subprocess.Popen[str]) -> None:
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        assert Running.poll() is None, "supervisor ended before grouped runner held"
        if FlagFile.is_file():
            return
        TimeClock.sleep(0.05)
    raise AssertionError("grouped runner did not write its start marker")


def SetGroupFloor(RootPath: FilePath, FloorMib: int) -> None:
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    Registry["runners"]["fixture.decode"]["group_peak_memory_mib"] = FloorMib
    Registry["runners"]["fixture.decode"]["max_memory_mib"] = FloorMib
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")


def SetBatchSlots(RootPath: FilePath, Capacity: int) -> None:
    ConfigFile = RootPath / "Supervisor.json"
    ConfigInfo = JsonCodec.loads(ConfigFile.read_text(encoding="utf-8"))
    ConfigInfo["resources"] = {"fixture:slots": Capacity}
    _ = ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    ResultInfo = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(RootPath / "Store"),
            "resource",
            "fixture:slots",
            "--available",
            "--capacity",
            str(Capacity),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
