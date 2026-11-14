from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import executable as KPythonPath

from tests.Research.Cli.ResearchClient import KResearchRoot
from tests.Research.SupervisorClient import FixtureJob, SessionHost


def CheckPoolBridge(TmpPath: FilePath) -> None:
    Harness = SessionHost(TmpPath, {"decode": 1}, {"fixture.decode": "decode"})
    Harness.Command = [
        KPythonPath,
        "-m",
        "convert",
        "research",
        "--root",
        str(KResearchRoot),
        "supervisor",
        "--config",
        str(Harness.ConfigFile),
    ]
    Harness.SubmitJobs(
        [FixtureJob("cli:hold", "fixture.decode", options={"mode": "sleep-first"})]
    )
    First = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
    try:
        _ = Harness.WaitSession("cli:hold")
        _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=4)
        _ = Harness.RunCli("pause", "decode", "--reason", "cli pause")
        Harness.WaitReason("cli:hold", "session stopped: pool_paused")
        assert (
            LoadJson(Harness.RunCli("status"))["pools"]["decode"]["paused"]["reason"]
            == "cli pause"
        )
        _ = Harness.RunCli("resume", "decode")
        _ = First.communicate(timeout=90)
    finally:
        if First.poll() is None:
            First.kill()
        _ = First.wait()
    assert First.returncode == 0
    assert Harness.ReadJob("cli:hold")["state"] == "completed"
    assert Harness.ReadResult("cli:hold")["result"]
