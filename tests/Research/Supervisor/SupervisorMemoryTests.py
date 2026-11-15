import json as JsonCodec
import os as OsLayer
import signal as Signals
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.MemoryHost import MakeMemoryHost
from tests.Research.SupervisorClient import FixtureJob, IsGoneByTimeout


def CheckMemoryStop() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeMemoryHost(RootPath)
        ChildFile = RootPath / "Child.pid"
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "memory:child",
                    "fixture.decode",
                    max_attempts=1,
                    options={"child_pid_path": str(ChildFile)},
                )
            ]
        )
        try:
            _ = Harness.RunIdle()
            Stopped = Harness.ReadJob("memory:child")
            Receipt = JsonCodec.loads(
                JsonCodec.dumps(Harness.ReadResult("memory:child"))
            )["receipt"]
            assert Stopped["state"] == "failed"
            assert Stopped["reason"] == "session stopped: memory_limit"
            assert Receipt["memory_limit_bytes"] == 64 * 1048576
            assert (
                Receipt["sampled_group_peak_memory_bytes"]
                > Receipt["memory_limit_bytes"]
            )
            assert IsGoneByTimeout(int(ChildFile.read_text(encoding="ascii")))
        finally:
            if ChildFile.is_file():
                ChildId = int(ChildFile.read_text(encoding="ascii"))
                if not IsGoneByTimeout(ChildId, Timeout=1):
                    OsLayer.kill(ChildId, Signals.SIGKILL)
