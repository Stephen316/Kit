import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinLogs() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = SessionHost(
            FilePath(TempPath), {"decode": 1}, {"fixture.decode": "decode"}
        )
        SetWinRunner(Harness)
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["max_log_bytes"] = 1024
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            [FixtureJob("windows:flood", "fixture.decode", options={"mode": "flood"})]
        )
        _ = Harness.RunIdle(IdleSeconds=1, MaxSeconds=90)
        assert Harness.ReadJob("windows:flood")["state"] == "completed"
        ReceiptInfo = JsonCodec.loads(
            JsonCodec.dumps(Harness.ReadResult("windows:flood"))
        )["receipt"]
        assert str(ReceiptInfo["process_start"]).startswith("windows:")
        assert ReceiptInfo["sampled_group_peak_memory_bytes"] > 0
        for LogInfo in ReceiptInfo["logs"].values():
            assert LogInfo["retained_bytes"] == 1024
            assert LogInfo["seen_bytes"] == 256 * 4096 * 6
            assert LogInfo["dropped_bytes"] == LogInfo["seen_bytes"] - 1024
