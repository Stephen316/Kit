import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.SupervisorClient import FixtureJob


# only the explicit candidate fingerprint permits a dependency to run before hosted verification
def CheckPendingCandidateInvalidation(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    Definition = TmpPath / "Jobs.json"
    Payload = TmpPath / "Input.json"
    _ = Payload.write_text('{"ci":"pending"}', encoding="utf-8")
    _ = Client.RunCli("bind", "ci:candidate", str(Payload))
    OptIn = {"dependency": "candidate", "candidate_fingerprint": True}
    Jobs = [
        FixtureJob(
            "candidate",
            "fixture.verify",
            inputs={"ci": "ci:candidate"},
            lease_seconds=30,
        ),
        FixtureJob(
            "dependent",
            "fixture.compare",
            depends_on=["candidate"],
            inputs={"candidate": OptIn},
            lease_seconds=30,
        ),
        FixtureJob(
            "active",
            "fixture.compare",
            depends_on=["candidate"],
            inputs={"candidate": OptIn},
            lease_seconds=30,
        ),
        FixtureJob(
            "ordinary",
            "fixture.compare",
            depends_on=["candidate"],
            inputs={"result": {"dependency": "candidate"}},
        ),
        FixtureJob("grandchild", "fixture.compare", depends_on=["dependent"]),
    ]
    _ = Definition.write_text(JsonCodec.dumps({"jobs": Jobs}), encoding="utf-8")
    _ = Client.RunCli("submit-batch", str(Definition))
    CandidateLease = Claim(Client, TmpPath, "candidate")
    Finish(Client, CandidateLease, Payload, "waiting_ci")
    Candidate = JsonCodec.loads(Client.RunCli("status", "--job", "candidate"))["jobs"][
        0
    ]
    assert Candidate["state"] == "waiting_ci"
    DependentLease = Claim(Client, TmpPath, "dependent")
    ClaimRecord = JsonCodec.loads(DependentLease.read_text(encoding="utf-8"))
    assert (
        ClaimRecord["snapshot"]["inputs"]["candidate"]["sha256"]
        == Candidate["fingerprint"]
    )
    Finish(Client, DependentLease, Payload, "completed")
    ActiveLease = Claim(Client, TmpPath, "active")
    Before = {
        Item["id"]: Item for Item in JsonCodec.loads(Client.RunCli("status"))["jobs"]
    }
    assert Before["dependent"]["state"] == "completed"
    assert Before["dependent"]["waiting_ci_inputs"] == {
        "candidate": Candidate["fingerprint"]
    }
    assert (
        Before["ordinary"]["state"]
        == Before["grandchild"]["state"]
        == "waiting_evidence"
    )

    _ = Payload.write_text('{"ci":"terminal"}', encoding="utf-8")
    _ = Client.RunCli("bind", "ci:candidate", str(Payload))
    After = {
        Item["id"]: Item for Item in JsonCodec.loads(Client.RunCli("status"))["jobs"]
    }
    assert After["candidate"]["state"] == "queued"
    for Name in ("dependent", "active"):
        assert After[Name]["state"] == "waiting_evidence"
        assert After[Name]["generation"] == Before[Name]["generation"] + 1
        assert After[Name]["receipt"] is None and After[Name]["result"] is None
        assert "waiting_ci_inputs" not in After[Name]
    Finish(Client, ActiveLease, Payload, "completed", ExitCode=3)

    VerdictLease = Claim(Client, TmpPath, "candidate", "rejected")
    Finish(Client, VerdictLease, Payload, "rejected")
    Final = {
        Item["id"]: Item for Item in JsonCodec.loads(Client.RunCli("status"))["jobs"]
    }
    assert Final["candidate"]["state"] == "rejected"
    assert all(
        Final[Name]["state"] == "waiting_evidence"
        for Name in ("active", "dependent", "ordinary", "grandchild")
    )

    _ = Payload.write_text('{"ci":"new-candidate"}', encoding="utf-8")
    _ = Client.RunCli("bind", "ci:candidate", str(Payload))
    AcceptedLease = Claim(Client, TmpPath, "candidate", "accepted")
    Finish(Client, AcceptedLease, Payload, "completed")
    Verified = {
        Item["id"]: Item for Item in JsonCodec.loads(Client.RunCli("status"))["jobs"]
    }
    assert Verified["candidate"]["state"] == "completed"
    assert all(
        Verified[Name]["state"] == "queued"
        for Name in ("active", "dependent", "ordinary")
    )
    assert "waiting_ci_inputs" not in Verified["dependent"]


# the persisted claim is the identifier for settling or fencing the exact execution
def Claim(
    Client: JobClient, RootPath: FilePath, Name: str, Stage: str = "first"
) -> FilePath:
    LeasePath = RootPath / f"{Name}-{Stage}.json"
    Response = JsonCodec.loads(
        Client.RunCli("claim", "--worker", "fixture:ci", "--claim-file", str(LeasePath))
    )
    assert Response["job"] == Name
    return LeasePath


# every state assertion follows real controller settlement with an immutable result
def Finish(
    Client: JobClient,
    LeasePath: FilePath,
    Payload: FilePath,
    Outcome: str,
    ExitCode: int = 0,
) -> None:
    _ = Client.RunCli(
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(Payload),
        "--outcome",
        Outcome,
        "--reason",
        "fixture CI dependency",
        ExitCode=ExitCode,
    )
