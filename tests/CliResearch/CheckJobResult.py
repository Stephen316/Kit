from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.CliResearch.ResearchClient import ResearchCli


# pool restart coverage needs evidence that the resumed worker actually published a durable result
def CheckJobResult(WorkPath: FilePath, ConfigPath: FilePath) -> None:
    Finished = ResearchCli(
        WorkPath, "supervisor", "--config", str(ConfigPath), "jobs", "--job", "cli:hold"
    )
    assert Finished.returncode == 0, Finished.stderr
    JobInfo = LoadJson(Finished.stdout)["jobs"][0]
    assert JobInfo["state"] == "completed"
    ResultHash = JobInfo["result"]
    Result = LoadJson(
        (WorkPath / "Store/objects" / ResultHash[:2] / ResultHash).read_bytes()
    )
    assert Result["result"]
