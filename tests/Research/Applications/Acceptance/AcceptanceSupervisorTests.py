import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.Acceptance.AcceptanceHost import AcceptanceHost
from tests.Research.Applications.DispatchHost import KRepoRoot
from tests.Research.Applications.RunQueueHost import RunQueueHost
from tests.Research.SupervisorClient import FixtureJob


# the trusted binding must originate in the registry independently of the runner arguments
def BindOwner(Harness: AcceptanceHost, ConfigName: str) -> None:
    RegistryPath = Harness.Dispatch.RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    Registry["runners"]["fixture.capture"]["application_installation"] = ConfigName
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")


# a later controller owner must fence a delayed acknowledgement from the older owner
def SetOwner(Harness: AcceptanceHost, OwnerName: str) -> None:
    Result = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(Harness.Supervisor.StorePath),
            "rotate-owner",
            "--new-owner",
            OwnerName,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Result.returncode == 0, Result.stderr


# the supervisor must release only the accepted spool and preserve restart ownership
def CheckHandoff() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve(), "handoff")
        BindOwner(Harness, Harness.Dispatch.ConfigFile.name)
        with RunQueueHost(Harness.Dispatch):
            Events = Harness.Run()
            (Finished,) = tuple(
                Event for Event in Events if Event.get("event") == "finished"
            )
            (AckEvent,) = tuple(
                Event
                for Event in Events
                if Event.get("event") == "application_acknowledgement"
            )
            assert Events.index(Finished) < Events.index(AckEvent)
            assert Finished["outcome"] == "completed"
            assert Finished["stale"] is False
            assert AckEvent["job"] == Harness.JobName
            assert AckEvent["attempt"] == Finished["attempt"]
            assert AckEvent["status"] == "acknowledged"
            assert AckEvent["restart_retained"] is True
            assert not list((Harness.Dispatch.Endpoint / "jobs").iterdir())
            Fence = Harness.Dispatch.Endpoint / "fence.json"
            assert JsonCodec.loads(Fence.read_bytes())["reason"] == "restart_required"


# two counted application jobs must resume under a fresh host only after durable acceptance
def CheckNextHost(TmpPath: FilePath) -> None:
    Harness = AcceptanceHost(TmpPath.resolve(), "handoff")
    FollowName = "fixture:after-restart"
    BindOwner(Harness, Harness.Dispatch.ConfigFile.name)
    DefineRestart(Harness, FollowName)
    with Harness.Supervisor.StartRun(
        "--idle-seconds", "2", "--max-seconds", "80"
    ) as Running:
        try:
            with RunQueueHost(Harness.Dispatch) as OldOwner:
                Before = WaitOldFence(Harness, FollowName, OldOwner)
            with RunQueueHost(Harness.Dispatch) as NewOwner:
                assert NewOwner != OldOwner
                OutputText, ErrorText = Running.communicate(timeout=80)
                assert Running.returncode == 0, OutputText + ErrorText
                VerifySequence(Harness, FollowName, OutputText, NewOwner)
            assert Harness.Supervisor.ReadJob(Harness.JobName) == Before
        finally:
            if Running.poll() is None:
                Running.kill()
            _ = Running.communicate(timeout=15)


# both phases must share one counted resource in the real private controller
def DefineRestart(Harness: AcceptanceHost, FollowName: str) -> None:
    ResourceName = "application:fixture"
    ResourceResult = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(Harness.Supervisor.StorePath),
            "resource",
            ResourceName,
            "--capacity",
            "1",
            "--available",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert ResourceResult.returncode == 0, ResourceResult.stderr
    Shared = {"lease_seconds": 30, "resources": [ResourceName]}
    Harness.Supervisor.SubmitJobs(
        [
            FixtureJob(
                Harness.JobName,
                "fixture.capture",
                options={"mode": "handoff"},
                **Shared,
            ),
            FixtureJob(
                FollowName,
                "fixture.capture",
                depends_on=[Harness.JobName],
                inputs={"prior": {"dependency": Harness.JobName}},
                options={"mode": "after_restart"},
                **Shared,
            ),
        ]
    )


# the next claim must wait without publishing requests while the prior owner remains alive
def WaitOldFence(
    Harness: AcceptanceHost, FollowName: str, OldOwner: dict[str, object]
) -> dict[str, object]:
    Endpoint = Harness.Dispatch.Endpoint
    MarkerPath = Harness.Dispatch.WaitFile("restart-wait.json")
    First = Harness.Supervisor.ReadJob(Harness.JobName)
    assert First["state"] == "completed" and First["attempts"] == 1
    assert (
        JsonCodec.loads(MarkerPath.read_bytes())["prior_result_sha256"]
        == First["result"]
    )
    Accepted = JsonCodec.loads(
        JsonCodec.dumps(Harness.Supervisor.ReadResult(Harness.JobName))
    )["result"]["records"]
    assert Accepted["host"] == OldOwner
    assert (
        JsonCodec.loads((Endpoint / "fence.json").read_bytes())
        == Accepted["restart_handoff"]
    )
    assert Harness.Supervisor.ReadJob(FollowName)["state"] == "running"
    assert list((Endpoint / "jobs").iterdir()) == []
    return First


# durable events must order acknowledgement before the next claim and name the replacement host
def VerifySequence(
    Harness: AcceptanceHost,
    FollowName: str,
    OutputText: str,
    NewOwner: dict[str, object],
) -> None:
    Events = [JsonCodec.loads(LineText) for LineText in OutputText.splitlines()]
    Actions = {"started", "finished", "application_acknowledgement"}
    Activity = [Event for Event in Events if Event.get("event") in Actions]
    assert [(Event["event"], Event["job"]) for Event in Activity] == [
        ("started", Harness.JobName),
        ("finished", Harness.JobName),
        ("application_acknowledgement", Harness.JobName),
        ("started", FollowName),
        ("finished", FollowName),
        ("application_acknowledgement", FollowName),
    ]
    assert all(Event["attempt"] == 1 for Event in Activity)
    assert Activity[2]["restart_retained"] is True
    assert Activity[5]["restart_retained"] is False
    assert Harness.Supervisor.ReadJob(FollowName)["state"] == "completed"
    Accepted = JsonCodec.loads(
        JsonCodec.dumps(Harness.Supervisor.ReadResult(FollowName))
    )["result"]["records"]
    assert Accepted["host"] == NewOwner
    assert Accepted["native_qualified"] is False
    assert list((Harness.Dispatch.Endpoint / "jobs").iterdir()) == []


# a separately configured owner mismatch must not erase the accepted output or its fence
def CheckMismatch() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve())
        OwnerPath = Harness.Dispatch.RootPath / "OtherInstallation.json"
        OwnerInfo = JsonCodec.loads(Harness.Dispatch.ConfigFile.read_bytes())
        OwnerInfo["installation"] = "fixture:other-owner"
        _ = OwnerPath.write_text(JsonCodec.dumps(OwnerInfo), encoding="utf-8")
        BindOwner(Harness, OwnerPath.name)
        with RunQueueHost(Harness.Dispatch):
            Events = Harness.Run()
            (Refusal,) = tuple(
                Event
                for Event in Events
                if Event.get("event") == "application_acknowledgement_failed"
            )
            assert "fence does not match" in str(Refusal["error"])
            assert Refusal["job"] == Harness.JobName
            JobInfo = Harness.Supervisor.ReadJob(Harness.JobName)
            assert JobInfo["state"] == "completed"
            assert JobInfo["attempts"] == 1
            (Spool,) = (Harness.Dispatch.Endpoint / "jobs").iterdir()
            assert (Spool / "fixture.bin").is_file()
            assert (Harness.Dispatch.Endpoint / "fence.json").is_file()
            assert Harness.Reconcile()["status"] == "acknowledged"


# delayed handoffs must match the current supervisor owner and exact accepted attempt
def CheckClaimFence() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve())
        with RunQueueHost(Harness.Dispatch):
            Spool = Harness.Accept()
            JobInfo = Harness.Supervisor.ReadJob(Harness.JobName)
            AttemptNumber = JobInfo["attempts"]
            assert isinstance(AttemptNumber, int)
            OwnerName = "a" * 64
            SetOwner(Harness, OwnerName)
            ClaimInfo = {
                "owner": OwnerName,
                "generation": JobInfo["generation"],
                "fingerprint": JobInfo["fingerprint"],
                "attempts": AttemptNumber,
            }
            Fence = Harness.Dispatch.Endpoint / "fence.json"
            Before = Fence.read_bytes()
            _ = Harness.Reconcile(
                ExitCode=1, ClaimInfo={**ClaimInfo, "owner": "b" * 64}
            )
            _ = Harness.Reconcile(
                ExitCode=1, ClaimInfo={**ClaimInfo, "attempts": AttemptNumber + 1}
            )
            assert Fence.read_bytes() == Before
            assert (Spool / "fixture.bin").is_file()
            assert Harness.Reconcile(ClaimInfo=ClaimInfo)["status"] == "acknowledged"
            assert not Spool.exists()
