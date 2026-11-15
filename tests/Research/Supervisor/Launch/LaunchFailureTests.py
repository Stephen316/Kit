import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Launch.LaunchHost import KFixturePath
from tests.Research.SupervisorClient import FixtureJob, SessionHost


def CheckGateError() -> None:
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
        Harness.SubmitJobs([FixtureJob("launch:failure", "fixture.decode")])
        ResultInfo = Subprocess.run(
            [
                System.executable,
                str(KFixturePath),
                "metadata-failure",
                "--root",
                str(RootPath),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        assert (
            JsonCodec.loads(ResultInfo.stdout.splitlines()[-1])["bootstrap_stopped"]
            is True
        )
        assert not (RootPath / "worker-entered.json").exists()
