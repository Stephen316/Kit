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


# an abrupt exit at the actual controller call preserves the normal settlement order
def CrashFinish(Harness: AcceptanceHost, BeforeCommit: bool) -> None:
    Wrapper = Harness.Dispatch.RootPath / "CrashFinish.py"
    _ = Wrapper.write_text(
        """import os
import sys
sys.path.insert(0, sys.argv.pop(1))
before = sys.argv.pop(1) == 'before'
from Adapters import A03Adapter
from Supervisor import main

finish = A03Adapter.FinishJob
def crash(self, path, outcome, result, reason):
    if outcome == 'completed' and before:
        os._exit(71)
    response = finish(self, path, outcome, result, reason)
    if outcome == 'completed' and response['stale'] is False:
        os._exit(71)
    return response

A03Adapter.FinishJob = crash
sys.exit(main())
""",
        encoding="utf-8",
    )
    First = Subprocess.run(
        [
            System.executable,
            str(Wrapper),
            str(KRepoRoot / "re/automation"),
            "before" if BeforeCommit else "after",
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
    assert First.returncode == 71, First.stdout + First.stderr


# recovery needs independently observed evidence from both sides of the durable finish
@TestMark.parametrize("CrashPoint", ("before", "after", "changed", "tampered"))
def CheckAckBoot(CrashPoint: str) -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = AcceptanceHost(RootPath, "handoff")
        BindOwner(Harness, Harness.Dispatch.ConfigFile.name)
        with RunQueueHost(Harness.Dispatch):
            SubmitFixture(Harness)
            CrashFinish(Harness, CrashPoint == "before")
            (Intent,) = (
                RootPath / "SupervisorState/application-acknowledgements"
            ).glob("*.json")
            (Spool,) = (Harness.Dispatch.Endpoint / "jobs").iterdir()
            CheckRecovery(Harness, CrashPoint, Intent, Spool)


# recovery must preserve the original fence if acceptance or source ownership changed
def CheckRecovery(
    Harness: AcceptanceHost, CrashPoint: str, IntentPath: FilePath, SpoolPath: FilePath
) -> None:
    Original = Harness.Supervisor.ReadJob(Harness.JobName)
    assert Original["state"] == ("running" if CrashPoint == "before" else "completed")
    assert Original["attempts"] == 1
    FencePath = Harness.Dispatch.Endpoint / "fence.json"
    OriginalFence = FencePath.read_bytes()
    ChangeInputs(Harness, CrashPoint, IntentPath)
    _ = Harness.Supervisor.RunCli(
        "pause", "application", "--reason", "fixture recovery"
    )
    Events = [
        CastValue(dict[str, object], Event) for Event in Harness.Supervisor.RunIdle()
    ]
    (Recovery,) = tuple(Event for Event in Events if Event.get("recovered") is True)
    assert Recovery["attempt"] == 1
    if CrashPoint == "after":
        assert Recovery["event"] == "application_acknowledgement"
        assert Recovery["restart_retained"] is True
        assert JsonCodec.loads(FencePath.read_bytes())["reason"] == "restart_required"
        assert not SpoolPath.exists()
        assert not IntentPath.exists()
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
