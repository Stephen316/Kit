from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.CliResearch.FixtureJob import FixtureJob
from tests.CliResearch.ResearchClient import ResearchCli


# changed source bindings must invalidate existing leases through the installed controller bridge
def CheckLeaseFlow(TmpPath: FilePath) -> None:
    Arguments = ("--store", str(TmpPath / "State"))
    Started = ResearchCli(TmpPath, "controller", *Arguments, "init")
    assert Started.returncode == 0, Started.stderr
    InputPath = TmpPath / "Input.bin"
    _ = InputPath.write_bytes(b"first")
    Bound = ResearchCli(
        TmpPath, "controller", *Arguments, "bind", "input:one", str(InputPath)
    )
    assert Bound.returncode == 0, Bound.stderr
    JobPath = TmpPath / "Job.json"
    JobInfo = FixtureJob("decode:one")
    JobInfo["inputs"] = {"source": "input:one"}
    _ = JobPath.write_text(DumpJson(JobInfo))
    Submitted = ResearchCli(TmpPath, "controller", *Arguments, "submit", str(JobPath))
    assert Submitted.returncode == 0, Submitted.stderr
    LeasePath = TmpPath / "Lease.json"
    Claimed = ResearchCli(
        TmpPath,
        "controller",
        *Arguments,
        "claim",
        "--worker",
        "cli:worker",
        "--claim-file",
        str(LeasePath),
    )
    assert Claimed.returncode == 0 and LeasePath.is_file(), Claimed.stderr
    _ = InputPath.write_bytes(b"changed")
    Changed = ResearchCli(
        TmpPath, "controller", *Arguments, "bind", "input:one", str(InputPath)
    )
    assert Changed.returncode == 0, Changed.stderr
    Stale = ResearchCli(
        TmpPath, "controller", *Arguments, "heartbeat", "--lease", str(LeasePath)
    )
    assert Stale.returncode == 3, Stale.stderr
    Status = ResearchCli(
        TmpPath, "controller", *Arguments, "status", "--job", "decode:one"
    )
    assert Status.returncode == 0, Status.stderr
    assert LoadJson(Status.stdout)["jobs"][0]["state"] == "queued"
