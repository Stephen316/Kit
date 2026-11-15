import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.Acceptance.AcceptanceHost import AcceptanceHost
from tests.Research.Applications.DispatchHost import KRepoRoot
from tests.Research.Applications.RunQueueHost import RunQueueHost


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
                Event for Event in Events if Event["event"] == "finished"
            )
            (AckEvent,) = tuple(
                Event
                for Event in Events
                if Event["event"] == "application_acknowledgement"
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
                if Event["event"] == "application_acknowledgement_failed"
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
