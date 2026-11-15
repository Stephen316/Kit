from json import loads as LoadJson
from pathlib import Path as FilePath
from time import monotonic as ReadClock, sleep as WaitBriefly

from tests.CliResearch.ResearchClient import ResearchCli


# pause assertions must wait for the actual worker termination record rather than race its shutdown
def WaitPause(WorkPath: FilePath, ConfigPath: FilePath) -> None:
    Deadline = ReadClock() + 30
    while ReadClock() < Deadline:
        Result = ResearchCli(
            WorkPath,
            "supervisor",
            "--config",
            str(ConfigPath),
            "jobs",
            "--job",
            "cli:hold",
        )
        assert Result.returncode == 0, Result.stderr
        if (
            LoadJson(Result.stdout)["jobs"][0]["reason"]
            == "session stopped: pool_paused"
        ):
            return
        WaitBriefly(0.1)
    raise AssertionError("configured worker was not stopped by pool pause")
