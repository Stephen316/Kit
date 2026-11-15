import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost


# windows resource reserves must block new claims and allow queued work when headroom returns
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinReserve() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = SessionHost(
            FilePath(TempPath), {"decode": 1}, {"fixture.decode": "decode"}
        )
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        Harness.SubmitJobs([FixtureJob("windows:reserve", "fixture.decode")])
        for KeyName, ReasonText in (
            ("reserved_cpus", "cpu headroom"),
            ("reserved_memory_mib", "memory headroom"),
        ):
            ConfigInfo["reserved_cpus"] = 65536 if KeyName == "reserved_cpus" else 0
            ConfigInfo["reserved_memory_mib"] = (
                1048576 if KeyName == "reserved_memory_mib" else 0
            )
            _ = Harness.ConfigFile.write_text(
                JsonCodec.dumps(ConfigInfo), encoding="utf-8"
            )
            Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=1)))
            assert any(EventInfo.get("reason") == ReasonText for EventInfo in Events)
            assert Harness.ReadJob("windows:reserve")["state"] == "queued"
        ConfigInfo["reserved_memory_mib"] = 0
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        _ = Harness.RunIdle(IdleSeconds=1)
        assert Harness.ReadJob("windows:reserve")["state"] == "completed"
