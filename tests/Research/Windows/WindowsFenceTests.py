import json as JsonCodec
import os as OsLayer
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import SessionHost
from tests.Research.Windows.IsProcessAlive import IsProcessAlive


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinFence() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        OrphanPath = RootPath / "SupervisorState" / "sessions" / "stale-pid"
        OrphanPath.mkdir(parents=True)
        _ = (OrphanPath / "session.json").write_text(
            JsonCodec.dumps(
                {
                    "pid": OsLayer.getpid(),
                    "process_start": "windows:wrong-start-time",
                    "job_object": "Local\\KitResearch-unowned",
                    "job_id": "stale-pid",
                    "attempt": 1,
                }
            ),
            encoding="utf-8",
        )
        _ = Harness.RunIdle(IdleSeconds=1)
        assert IsProcessAlive(OsLayer.getpid())
        assert not OrphanPath.exists()
