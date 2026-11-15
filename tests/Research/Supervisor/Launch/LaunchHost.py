import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

# launch probes must find their production entry point independently of the caller directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# launch assertions share the same production guest fixture across gate failure scenarios
KFixturePath = KRepoRoot / "re/automation/LaunchFixture.py"


# gate scenarios need an actual bootstrap connected to a controllable owner pipe
def StartGateHost(RootPath: FilePath) -> Subprocess.Popen[str]:
    return Subprocess.Popen(
        [System.executable, str(KFixturePath), "launch", "--root", str(RootPath)],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )


# termination scenarios need a verified process identity before checking bootstrap lifetime
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


# a stopped bootstrap can remain visible as a zombie before its parent reaps it
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
