import json as JsonCodec
import subprocess as Subprocess
import sys as System
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.ScopeWatchStub import GetBasePython
from tests.Research.Windows.WaitForExit import WaitForExit


# an unrelated process with the same executable must survive an owned hard timeout
@Pytest.mark.skipif(System.platform != "win32", reason="Windows scope job boundary")
def CheckScopeWatch(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "RunScope"
    RunPath.mkdir()
    Outside = Subprocess.Popen(
        [
            GetBasePython(),
            "-I",
            "-S",
            "-c",
            "import sys; sys.stdin.buffer.read()",
        ],
        stdin=Subprocess.PIPE,
    )
    try:
        RunWatchdog(RunPath)
        AssertDrained(RunPath, Outside.pid)
        assert Outside.poll() is None
    finally:
        assert Outside.stdin is not None
        Outside.stdin.close()
        try:
            _ = Outside.wait(timeout=10)
        except Subprocess.TimeoutExpired:
            Outside.kill()
            _ = Outside.wait(timeout=5)
            raise


# the real watchdog must stop a collector that never returns and its direct child
def RunWatchdog(RunPath: FilePath) -> None:
    Script = FilePath(__file__).with_name("ScopeWatchStub.py")
    Result = Subprocess.run(
        [
            System.executable,
            "-I",
            str(Script),
            "watch",
            str(RunPath),
            str(KRepoRoot / "re/automation"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr


# the durable records must tie the witnessed drain to the actual launch job
def AssertDrained(RunPath: FilePath, OutsidePid: int) -> None:
    LaunchBytes = (RunPath / "launch.json").read_bytes()
    Launch = JsonCodec.loads(LaunchBytes)
    Receipt = JsonCodec.loads((RunPath / "watchdog.json").read_bytes())
    MemberPids = JsonCodec.loads((RunPath / "fixture.json").read_bytes())
    assert Receipt["outcome"] == "timed_out" and Receipt["job_drained"] is True, Receipt
    assert Receipt["collector"] == Launch["collector"]
    assert Receipt["launch_sha256"] == HashBytes(LaunchBytes).hexdigest()
    assert Receipt["collector"]["pid"] == MemberPids["collector"]
    assert Receipt["collector"]["started"].startswith("windows:")
    assert set(MemberPids.values()) <= set(Receipt["members_before_stop"])
    assert OutsidePid not in Receipt["members_before_stop"] and "report" not in Receipt
    for ProcessId in MemberPids.values():
        WaitForExit(ProcessId)
