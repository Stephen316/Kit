import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[4]
KFixturePath = KRepoRoot / "re/automation/LaunchFixture.py"


def StartGateHost(RootPath: FilePath) -> Subprocess.Popen[str]:
    return Subprocess.Popen(
        [System.executable, str(KFixturePath), "launch", "--root", str(RootPath)],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )


def WaitBootstrap(RootPath: FilePath) -> int:
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        RecordFile = RootPath / "bootstrap.json"
        if RecordFile.is_file():
            RecordInfo = JsonCodec.loads(RecordFile.read_text(encoding="utf-8"))
            assert RecordInfo["identity"] is not None
            return int(RecordInfo["pid"])
        TimeClock.sleep(0.02)
    raise AssertionError("launch fixture did not create its bootstrap")


def WaitGateStop(ProcessId: int) -> None:
    Until = TimeClock.monotonic() + 40
    while TimeClock.monotonic() < Until:
        ResultInfo = Subprocess.run(
            ["/bin/ps", "-p", str(ProcessId), "-o", "stat="],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if ResultInfo.returncode == 1 and not ResultInfo.stdout.strip():
            return
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        if ResultInfo.stdout.strip().startswith("Z"):
            return
        TimeClock.sleep(0.1)
    raise AssertionError("bootstrap did not finish its bounded gate wait")
