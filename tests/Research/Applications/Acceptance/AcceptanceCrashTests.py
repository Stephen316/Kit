import hashlib as Hashing
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.Acceptance.AcceptanceHost import (
    AcceptanceHost,
    SubmitFixture,
)
from tests.Research.Applications.Acceptance.AcceptanceSupervisorTests import BindOwner
from tests.Research.Applications.DispatchHost import KRepoRoot
from tests.Research.Applications.RunQueueHost import RunQueueHost


# a process barrier at the controller call preserves the actual supervisor and application paths
def RunWrapped(
    Harness: AcceptanceHost, ModeValue: str
) -> "Subprocess.CompletedProcess[str]":
    Wrapper = Harness.Dispatch.RootPath / "CrashFinish.py"
    _ = Wrapper.write_text(
        """import os
import sys
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
mode = sys.argv.pop(1)
from Adapters import A03Adapter
from Supervisor import main

finish = A03Adapter.FinishJob
def crash(self, path, outcome, result, reason):
    if outcome == 'completed' and mode == 'before':
        os._exit(71)
    response = finish(self, path, outcome, result, reason)
    if outcome == 'completed' and response['stale'] is False:
        os._exit(71)
    return response

status = A03Adapter.ReadStatus
failed = False
def temporary(self, *args, **kwargs):
    global failed
    if not failed:
        failed = True
        Path(__file__).with_name('ControllerInterrupted').touch()
        raise OSError('fixture lost one controller response')
    return status(self, *args, **kwargs)

if mode == 'retry':
    A03Adapter.ReadStatus = temporary
else:
    A03Adapter.FinishJob = crash
sys.exit(main())
""",
        encoding="utf-8",
    )
    return Subprocess.run(
        [
            System.executable,
            str(Wrapper),
            str(KRepoRoot / "re/automation"),
            ModeValue,
            "--config",
            str(Harness.Supervisor.ConfigFile),
            "run",
            "--idle-seconds",
            "3",
            "--max-seconds",
            "60",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


# recovery needs independently observed evidence from both sides of the durable finish
@TestMark.parametrize(
    "CrashPoint",
    ("before", "after", "changed", "tampered", "registry", "replayed", "retry"),
)
def CheckAckBoot(CrashPoint: str) -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = AcceptanceHost(RootPath, "handoff")
        BindOwner(Harness, Harness.Dispatch.ConfigFile.name)
        with RunQueueHost(Harness.Dispatch):
            SubmitFixture(Harness)
            First = RunWrapped(Harness, "before" if CrashPoint == "before" else "after")
            assert First.returncode == 71, First.stdout + First.stderr
            (Intent,) = (
                RootPath / "SupervisorState/application-acknowledgements"
            ).glob("*.json")
            (Spool,) = (Harness.Dispatch.Endpoint / "jobs").iterdir()
            AssertRecovery(Harness, CrashPoint, Intent, Spool)


# recovery must preserve the original fence if acceptance or source ownership changed
def AssertRecovery(
    Harness: AcceptanceHost, CrashPoint: str, IntentPath: FilePath, SpoolPath: FilePath
) -> None:
    Original = Harness.Supervisor.ReadJob(Harness.JobName)
    assert Original["state"] == ("running" if CrashPoint == "before" else "completed")
    assert Original["attempts"] == 1
    if CrashPoint != "before":
        AssertStored(Harness, IntentPath)
    if CrashPoint == "replayed":
        assert Harness.Reconcile()["restart_retained"] is True
    FencePath = Harness.Dispatch.Endpoint / "fence.json"
    OriginalFence = FencePath.read_bytes()
    ChangeInputs(Harness, CrashPoint, IntentPath)
    _ = Harness.Supervisor.RunCli(
        "pause", "application", "--reason", "fixture recovery"
    )
    Events = RecoverRun(Harness, CrashPoint)
    (Recovery,) = tuple(Event for Event in Events if Event.get("recovered") is True)
    assert Recovery["attempt"] == 1
    if CrashPoint in ("after", "replayed", "retry"):
        AssertReleased(Recovery, CrashPoint, FencePath, IntentPath, SpoolPath)
        if CrashPoint == "replayed":
            assert FencePath.read_bytes() == OriginalFence
    else:
        EventName = (
            "application_acknowledgement_not_accepted"
            if CrashPoint == "before"
            else "application_acknowledgement_failed"
        )
        assert Recovery["event"] == EventName
        assert FencePath.read_bytes() == OriginalFence
        assert (SpoolPath / "fixture.bin").is_file()
        assert IntentPath.is_file() == (CrashPoint != "before")
    Current = Harness.Supervisor.ReadJob(Harness.JobName)
    assert Current["result"] == Original["result"] or CrashPoint == "before"
    assert Current["attempts"] == 1


# durable intake must retain the private intent binding alongside the accepted artifacts
def AssertStored(Harness: AcceptanceHost, IntentPath: FilePath) -> None:
    Intent = JsonCodec.loads(IntentPath.read_bytes())
    Canonical = JsonCodec.dumps(
        Intent, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    Digest = Hashing.sha256(Canonical.encode("utf-8")).hexdigest()
    Result = Harness.Supervisor.ReadResult(Harness.JobName)
    assert Result["application_acknowledgement_sha256"] == Digest
    assert Result["output_artifacts_version"] == 1


# a lost status response must recover under the same new controller ownership
def RecoverRun(Harness: AcceptanceHost, CrashPoint: str) -> list[dict[str, object]]:
    if CrashPoint != "retry":
        return [
            CastValue(dict[str, object], Event)
            for Event in Harness.Supervisor.RunIdle()
        ]
    Second = RunWrapped(Harness, "retry")
    assert Second.returncode == 0, Second.stdout + Second.stderr
    Events: list[dict[str, object]] = [
        JsonCodec.loads(LineText) for LineText in Second.stdout.splitlines()
    ]
    assert (Harness.Dispatch.RootPath / "ControllerInterrupted").is_file()
    return Events


# a replay after cleanup must preserve the older process restart fence
def AssertReleased(
    Recovery: dict[str, object],
    CrashPoint: str,
    FencePath: FilePath,
    IntentPath: FilePath,
    SpoolPath: FilePath,
) -> None:
    assert Recovery["event"] == "application_acknowledgement"
    if CrashPoint == "replayed":
        assert Recovery["status"] == "no_pending_acceptance"
    else:
        assert Recovery["status"] == "acknowledged"
        assert Recovery["restart_retained"] is True
    assert JsonCodec.loads(FencePath.read_bytes())["reason"] == "restart_required"
    assert not SpoolPath.exists()
    assert not IntentPath.exists()


# changing only configuration bytes or the local nonce must defeat the original binding
def ChangeInputs(
    Harness: AcceptanceHost, CrashPoint: str, IntentPath: FilePath
) -> None:
    if CrashPoint == "changed":
        Configuration = Harness.Dispatch.ConfigFile
        _ = Configuration.write_bytes(Configuration.read_bytes() + b"\n")
    if CrashPoint == "tampered":
        Intent = JsonCodec.loads(IntentPath.read_bytes())
        Intent["nonce"] = "0" * 64
        _ = IntentPath.write_text(JsonCodec.dumps(Intent), encoding="utf-8")
    if CrashPoint == "registry":
        RegistryPath = Harness.Dispatch.RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryPath.read_bytes())
        del Registry["runners"]["fixture.capture"]["application_installation"]
        _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
