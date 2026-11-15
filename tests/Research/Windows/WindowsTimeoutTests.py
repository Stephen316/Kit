import hashlib as Hashing
import json as JsonCodec
import os as OsLayer
import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# a real controller must retain the identity of the timed out request before any recovery is considered
@TestMark.skipif(OsLayer.name != "nt", reason="requires Windows application transport")
def CheckTimedLink() -> None:
    with TempFiles.TemporaryDirectory() as TempName:
        RootPath = FilePath(TempName).resolve()
        Queue = DispatchHost(RootPath)
        Config = JsonCodec.loads(Queue.ConfigFile.read_bytes())
        Config["application"] = "solidworks"
        _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
        Harness = SessionHost(RootPath, {"apps": 1}, {"fixture.app": "apps"})
        SetAppRunner(Harness, Queue.ConfigFile, Readback=True)
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "fixture:timeout",
                    "fixture.app",
                    lease_seconds=12,
                    timeout_seconds=15,
                    max_attempts=2,
                    resources=["application:missing"],
                    options={"source_revision": Config["source_revision"]},
                )
            ]
        )
        _ = Harness.RunIdle()
        (Spool,) = (Queue.Endpoint / "jobs").iterdir()
        AssertTimedLink(Harness, Spool)
        assert (Queue.Endpoint / "fence.json").is_file()
        assert not (Spool / "native-recovery.json").exists()


# the retained timeout must bind the specific controller result without creating successful outputs
def AssertTimedLink(Harness: SessionHost, SpoolPath: FilePath) -> None:
    JobInfo = Harness.ReadJob("fixture:timeout")
    Accepted = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("fixture:timeout")))
    RawRequest = (SpoolPath / "phase.request").read_bytes()
    Request = JsonCodec.loads(RawRequest)
    assert JobInfo["state"] == Accepted["result"]["outcome"] == "waiting_application"
    assert "output_artifacts" not in Accepted
    assert Accepted["result"]["records"]["queue_timeout"] == {
        "version": 1,
        "installation": Request["installation"],
        "queue_job_id": SpoolPath.name,
        "request_sha256": Hashing.sha256(RawRequest).hexdigest(),
        "nonce": Request["nonce"],
        "client": Request["client"],
        "source_revision": Request["source_revision"],
        "job_id": "fixture:timeout",
        "kind": "fixture.app",
        "resources": ["application:missing"],
        "session": Accepted["receipt"]["session"],
        "generation": JobInfo["generation"],
        "fingerprint": JobInfo["fingerprint"],
        "attempt": JobInfo["attempts"],
    }
