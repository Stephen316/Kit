from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Research.Cli.ResearchClient import ResearchCli
from tests.Research.SupervisorClient import FixtureJob


def CheckLeaseFlow(TmpPath: FilePath) -> None:
    StorePath = TmpPath / "State"
    Arguments = ("--store", str(StorePath))
    Started = ResearchCli("controller", *Arguments, "init")
    assert Started.returncode == 0, Started.stderr
    InputPath = TmpPath / "Input.bin"
    _ = InputPath.write_bytes(b"first")
    Bound = ResearchCli("controller", *Arguments, "bind", "input:one", str(InputPath))
    assert Bound.returncode == 0, Bound.stderr
    JobPath = TmpPath / "Job.json"
    _ = JobPath.write_text(
        DumpJson(
            FixtureJob("decode:one", "fixture.decode", inputs={"source": "input:one"})
        )
    )
    Submitted = ResearchCli("controller", *Arguments, "submit", str(JobPath))
    assert Submitted.returncode == 0, Submitted.stderr
    LeasePath = TmpPath / "Lease.json"
    Claimed = ResearchCli(
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
    Changed = ResearchCli("controller", *Arguments, "bind", "input:one", str(InputPath))
    assert Changed.returncode == 0, Changed.stderr
    Stale = ResearchCli(
        "controller", *Arguments, "heartbeat", "--lease", str(LeasePath)
    )
    assert Stale.returncode == 3, Stale.stderr
    Status = ResearchCli("controller", *Arguments, "status", "--job", "decode:one")
    assert Status.returncode == 0, Status.stderr
    assert LoadJson(Status.stdout)["jobs"][0]["state"] == "queued"
