import json as JsonCodec
import signal as Signals
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, IsGoneByTimeout, SessionHost
from tests.Research.Supervisor.WaitChildId import WaitChildId
from tests.Research.Supervisor.StopGroup import StopGroup


def CheckGroupStop() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        RegistryFile = RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
        Registry["runners"]["fixture.decode"]["argv"] = [
            System.executable,
            str(FilePath(__file__).with_name("GroupRunner.py")),
            "{session}",
        ]
        _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
        Harness.SubmitJobs([FixtureJob("group:stop", "fixture.decode", max_attempts=1)])
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
        ChildId = None
        ParentId = None
        try:
            SessionInfo = Harness.WaitSession("group:stop")
            ParentId = int(str(SessionInfo["pid"]))
            ChildId = WaitChildId(RootPath, str(SessionInfo["session"]))
            Running.send_signal(Signals.SIGKILL)
            _ = Running.communicate(timeout=30)
            Events = Harness.RunIdle()
            assert IsGoneByTimeout(ChildId)
            Orphans = [
                JsonCodec.loads(JsonCodec.dumps(Event))
                for Event in Events
                if JsonCodec.loads(JsonCodec.dumps(Event)).get("event") == "orphan"
            ]
            assert len(Orphans) == 1
            assert Orphans[0]["identity_matched"] is True
            assert Orphans[0]["stopped"] is True
        finally:
            Running.kill()
            _ = Running.wait()
            StopGroup(ParentId, ChildId)
