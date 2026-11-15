from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import PIPE as KPipe, Popen as StartProcess
from sys import executable as KPythonPath

from tests.CliResearch.CheckJobResult import CheckJobResult
from tests.CliResearch.FixtureJob import FixtureJob
from tests.CliResearch.PreparePool import PreparePool
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.CliResearch.WaitPause import WaitPause
from tests.CliResearch.WaitSession import WaitSession


# the installed bridge must preserve pool exclusivity and durable pause resume behavior
def CheckPoolBridge(TmpPath: FilePath) -> None:
    ConfigPath = PreparePool(TmpPath)
    Arguments = ("--config", str(ConfigPath))
    BatchPath = TmpPath / "Batch.json"
    _ = BatchPath.write_text(
        DumpJson({"jobs": [FixtureJob("cli:hold", HoldFirst=True)]})
    )
    Submitted = ResearchCli(TmpPath, "supervisor", *Arguments, "submit", str(BatchPath))
    assert Submitted.returncode == 0, Submitted.stderr
    First = StartProcess(
        (
            KPythonPath,
            "-I",
            "-m",
            "KitCli",
            "research",
            "--root",
            str(ResearchRoot()),
            "supervisor",
            *Arguments,
            "run",
            "--idle-seconds",
            "15",
            "--max-seconds",
            "60",
        ),
        cwd=TmpPath,
        stdout=KPipe,
        stderr=KPipe,
        text=True,
    )
    try:
        WaitSession(TmpPath)
        Blocked = ResearchCli(
            TmpPath, "supervisor", *Arguments, "run", "--idle-seconds", "1"
        )
        assert Blocked.returncode == 4, Blocked.stderr
        Paused = ResearchCli(
            TmpPath,
            "supervisor",
            *Arguments,
            "pause",
            "decode",
            "--reason",
            "cli pause",
        )
        assert Paused.returncode == 0, Paused.stderr
        WaitPause(TmpPath, ConfigPath)
        Status = ResearchCli(TmpPath, "supervisor", *Arguments, "status")
        assert Status.returncode == 0, Status.stderr
        assert (
            LoadJson(Status.stdout)["pools"]["decode"]["paused"]["reason"]
            == "cli pause"
        )
        Resumed = ResearchCli(TmpPath, "supervisor", *Arguments, "resume", "decode")
        assert Resumed.returncode == 0, Resumed.stderr
        _, ErrorText = First.communicate(timeout=90)
        assert First.returncode == 0, ErrorText
    finally:
        if First.poll() is None:
            First.kill()
        _ = First.wait()
    CheckJobResult(TmpPath, ConfigPath)
