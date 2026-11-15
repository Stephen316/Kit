import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Launch.LaunchHost import KFixturePath
from tests.Research.Supervisor.StopGroup import StopGroup
from tests.Research.SupervisorClient import FixtureJob, IsGoneByTimeout, SessionHost


# successful launch must preserve one identity across the worker metadata and published receipt
def CheckGateExec() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        RegistryFile = RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
        Registry["runners"]["fixture.decode"]["argv"] = [
            System.executable,
            str(KFixturePath),
            "supervised",
            "--root",
            str(RootPath),
        ]
        _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
        Harness.SubmitJobs([FixtureJob("launch:proof", "fixture.decode")])
        try:
            _ = Harness.RunIdle()
            assert Harness.ReadJob("launch:proof")["state"] == "completed"
            Executed = JsonCodec.loads(
                (RootPath / "executed.json").read_text(encoding="utf-8")
            )
            Receipt = JsonCodec.loads(
                JsonCodec.dumps(Harness.ReadResult("launch:proof"))
            )["receipt"]
            assert Executed["pid"] == Executed["metadata"]["pid"] == Receipt["pid"]
            assert Executed["metadata"]["process_start"] == Receipt["process_start"]
            assert IsGoneByTimeout(Executed["child"])
        finally:
            if (RootPath / "executed.json").is_file():
                Executed = JsonCodec.loads(
                    (RootPath / "executed.json").read_text(encoding="utf-8")
                )
                StopGroup(Executed["pid"], Executed["child"])
