import json as JsonCodec
import sys as System
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# a real macos request timeout must preserve exact custody without starting a cad host
@TestMark.skipif(System.platform != "darwin", reason="Fusion worker host boundary")
def CheckFusionWait(TmpPath: FilePath) -> None:
    Queue = DispatchHost(TmpPath.resolve())
    Harness = SessionHost(Queue.RootPath, {"apps": 1}, {"fixture.app": "apps"})
    SetAppRunner(Harness, Queue.ConfigFile)
    Installation = JsonCodec.loads(Queue.ConfigFile.read_bytes())
    PlanBytes = JsonCodec.dumps(
        {"source_revision": Installation["source_revision"]}
    ).encode("utf-8")
    Harness.BindBytes("fixture:plan", PlanBytes)
    Harness.SubmitJobs(
        [
            FixtureJob(
                "unanswered",
                "fixture.app",
                timeout_seconds=15,
                lease_seconds=6,
                resources=["application:missing"],
                options={"phase": "a"},
                inputs={"plan": "fixture:plan"},
            )
        ]
    )
    _ = Harness.RunIdle(IdleSeconds=1, MaxSeconds=45)
    Status = Harness.ReadJob("unanswered")
    assert Status["state"] == "waiting_application", Status
    VerifyTimeout(Queue.Endpoint, Harness.ReadResult("unanswered"), PlanBytes)


# only the existing owned request can explain the terminal parked attempt
def VerifyTimeout(
    Endpoint: FilePath, Accepted: dict[str, object], PlanBytes: bytes
) -> None:
    (RequestPath,) = Endpoint.glob("jobs/*/probe.request")
    RequestBytes = RequestPath.read_bytes()
    Request = JsonCodec.loads(RequestBytes)
    Result = JsonCodec.loads(JsonCodec.dumps(Accepted["result"]))
    Records = Result["records"]
    assert Records["queue_timeout"] == {
        "version": 1,
        "queue_job_id": RequestPath.parent.name,
        "request_sha256": HashBytes(RequestBytes).hexdigest(),
        "source_revision": Request["source_revision"],
        "operation": "probe",
        "plan_sha256": HashBytes(PlanBytes).hexdigest(),
    }
    Fence = JsonCodec.loads((Endpoint / "fence.json").read_bytes())
    assert Fence["job_id"] == RequestPath.parent.name
    assert Fence["reason"] == "quarantined"
    assert (RequestPath.parent / "cancel.json").is_file()
    assert Records["native_qualified"] is False
    assert "output_artifacts" not in Accepted
    assert "application_rearm_intent_sha256" not in Accepted
