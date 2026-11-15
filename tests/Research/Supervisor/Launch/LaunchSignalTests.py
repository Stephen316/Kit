import json as JsonCodec
import signal as Signals
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as Pytest

from tests.Research.Supervisor.Launch.LaunchHost import KFixturePath
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# closing a launch reader must retain the operating system signal needed for diagnosis
def CheckGatePipe() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            [
                System.executable,
                str(KFixturePath),
                "pipe-signal",
                "--root",
                str(FilePath(TempPath)),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        assert JsonCodec.loads(ResultInfo.stdout)["signal"] == Signals.SIGPIPE


# the real supervisor must arm before releasing a worker and settle an ordinary signal kill without memory backoff
@Pytest.mark.skipif(System.platform != "linux", reason="Linux kernel observer boundary")
def CheckPlainKill(TmpPath: FilePath) -> None:
    Harness = SessionHost(TmpPath, {"decode": 4}, {"fixture.decode": "decode"})
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    Config["adaptive_limits"] = True
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    RegistryPath = TmpPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    Command = [System.executable, str(KFixturePath)]
    RootArgs = ["--root", str(TmpPath)]
    Registry["runners"]["fixture.decode"]["argv"] = (
        Command + ["ordinary-sigkill"] + RootArgs
    )
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Harness.SubmitJobs([FixtureJob("linux:ordinary", "fixture.decode", max_attempts=1)])
    ResultInfo = Subprocess.run(
        Command + ["observe-signal"] + RootArgs,
        capture_output=True,
        text=True,
        check=False,
        env=Harness.Environment,
        timeout=45,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    Events = [
        JsonCodec.loads(EventLine) for EventLine in ResultInfo.stdout.splitlines()
    ]
    Names = [Event.get("event") for Event in Events]
    assert Names.index("kernel_observer_armed") < Names.index("started")
    assert (
        Names.index("kernel_observer_reaped")
        < Names.index("kernel_observer_closed")
        < Names.index("finished")
    )
    assert "adaptive_backoff" not in Names
    assert Harness.ReadJob("linux:ordinary")["state"] == "failed"
    Receipt = CastValue(
        dict[str, object], Harness.ReadResult("linux:ordinary")["receipt"]
    )
    assert Receipt["signal"] == Signals.SIGKILL and Receipt["stop_reason"] is None
    assert "kernel_oom" not in Receipt
