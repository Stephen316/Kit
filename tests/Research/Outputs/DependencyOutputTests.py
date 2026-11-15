import hashlib as Hashing
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Outputs.SetOutputRunner import SetOutputRunner
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# the application handoff needs independent producer and digest checking processes
def BuildHandoff(RootPath: FilePath) -> SessionHost:
    Harness = SessionHost(
        RootPath,
        {"capture": 1, "consume": 1},
        {"fixture.output": "capture", "fixture.decode": "consume"},
    )
    SetOutputRunner(Harness, "fixture.output")
    Harness.BindBytes("capture:source", b"original capture inputs")
    Harness.BindBytes("capture:plan", b"pinned capture plan")
    Harness.BindBytes("native", b"unrelated global name")
    return Harness


# the dependent worker must receive every requested role from the current accepted generation
def HandoffJobs(ArtifactRole: str = "native") -> list[dict[str, object]]:
    return [
        FixtureJob(
            "capture:a",
            "fixture.output",
            inputs={"source": "capture:source"},
            lease_seconds=30,
        ),
        FixtureJob(
            "capture:b",
            "fixture.decode",
            inputs={
                "phase-a.accepted": {"dependency": "capture:a"},
                "phase-a.native": {"dependency": "capture:a", "artifact": ArtifactRole},
                "plan": "capture:plan",
            },
            depends_on=["capture:a"],
            lease_seconds=30,
        ),
    ]


# digest verification in the consumer distinguishes a current result from a stale or global binding
def AssertReceipt(Harness: SessionHost) -> dict[str, object]:
    Parent = Harness.ReadJob("capture:a")
    Child = Harness.ReadJob("capture:b")
    assert Parent["state"] == Child["state"] == "completed"
    ProducerResult = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("capture:a")))
    ConsumerResult = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("capture:b")))
    assert ConsumerResult["result"]["records"]["inputs"] == [
        Parent["result"],
        ProducerResult["output_artifacts"]["native"]["sha256"],
        Hashing.sha256(b"pinned capture plan").hexdigest(),
    ]
    return Child


# repeated submissions must reuse current results while a new accepted parent invalidates the child
def CheckHandoff() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = BuildHandoff(FilePath(TempPath).resolve())
        Harness.SubmitJobs(HandoffJobs())
        assert Harness.ReadJob("capture:b")["state"] == "waiting_evidence"
        _ = Harness.RunIdle()
        First = AssertReceipt(Harness)
        Harness.SubmitJobs(HandoffJobs())
        _ = Harness.RunIdle(IdleSeconds=0.5)
        assert Harness.ReadJob("capture:b") == First
        Harness.BindBytes("capture:source", b"changed capture inputs")
        Waiting = Harness.ReadJob("capture:b")
        assert Waiting["state"] == "waiting_evidence"
        assert Waiting["attempts"] == 0
        assert Waiting["result"] is None
        _ = Harness.RunIdle()
        Second = AssertReceipt(Harness)
        assert Second["result"] != First["result"]
        assert Second["generation"] != First["generation"]


# a missing output role must keep the entire recipe pending even if the global name exists
def CheckMissing() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = BuildHandoff(FilePath(TempPath).resolve())
        Harness.BindBytes("unpublished", b"unrelated global fallback")
        Harness.SubmitJobs(HandoffJobs("unpublished"))
        _ = Harness.RunIdle()
        assert Harness.ReadJob("capture:a")["state"] == "completed"
        Waiting = Harness.ReadJob("capture:b")
        assert Waiting["state"] == "waiting_evidence"
        assert Waiting["attempts"] == 0
        assert Waiting["result"] is None
        assert not any((Harness.RootPath / "SupervisorState/claims").iterdir())


# a producer must be in the explicit dependency graph before its artifacts can be selected
def CheckSelectors() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = BuildHandoff(FilePath(TempPath).resolve())
        Producer, Child = HandoffJobs()
        JobFile = Harness.RootPath / "InvalidJobs.json"
        _ = JobFile.write_text(
            JsonCodec.dumps({"jobs": [Producer, {**Child, "depends_on": []}]}),
            encoding="utf-8",
        )
        _ = Harness.RunCli("submit", str(JobFile), ExitCode=1)
        Status = JsonCodec.loads(Harness.RunCli("jobs"))
        assert Status["jobs"] == []
