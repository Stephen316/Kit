# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import sqlite3 as SqlCodec
import sys as System
from contextlib import closing as CloseConnection
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Applications.FusionPhaseQueueTests import (
    InterruptQueue,
    MakeQueueHost,
    PreparePair,
    RunFusionTool,
    VerifyPhaseJobs,
)
from tests.Research.SupervisorClient import SessionHost


# the windows queue must recover the exact committed pair without editing its ledger
@Pytest.mark.skipif(System.platform != "win32", reason="Windows receipt custody")
def CheckReceipt(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Prepared"
    PlanReceipt = PreparePair(OutputPath, False)
    Harness = MakeQueueHost(TmpPath, PlanReceipt["source_revision"])
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    OwnerPath = TmpPath.resolve() / "Private"
    OwnerPath.mkdir()
    ReceiptPath = OwnerPath / "QueueReceipt.json"
    IntentPath = OwnerPath / ".QueueReceipt.json.intent.json"
    QueuePath = "re/automation/ApplicationWorkers/QueueFusionPhases.py"
    Config = ["--config", str(Harness.ConfigFile)]
    PlanPath = OutputPath / "plan.json"
    Arguments = Config + [
        "--resource",
        "application:fusion:local",
        "--plan",
        str(PlanPath),
        "--receipt",
        str(ReceiptPath),
    ]
    Recovery = Config + ["--recover-receipt", str(ReceiptPath)]

    InterruptQueue(QueuePath, Arguments, "before-ledger")
    Intent = IntentPath.read_bytes()
    VerifyPending(QueuePath, Recovery, ReceiptPath, DatabasePath)

    InterruptQueue(QueuePath, Arguments, "before-receipt")
    Ledger = DatabasePath.read_bytes()
    assert not ReceiptPath.exists() and IntentPath.read_bytes() == Intent
    _ = RunFusionTool(QueuePath, Arguments + ["--run", "conflict"], ExitCode=1)
    assert not ReceiptPath.exists()
    PlanPath.unlink()
    VerifyReplay(Harness, QueuePath, Recovery, ReceiptPath)
    assert IntentPath.read_bytes() == Intent and DatabasePath.read_bytes() == Ledger
    assert not (TmpPath / "AbsentEndpoint").exists()


# recovery must reconstruct the exact receipt on every invocation without the original plan
def VerifyReplay(
    Harness: SessionHost, QueuePath: str, Recovery: list[str], ReceiptPath: FilePath
) -> None:
    Output = RunFusionTool(QueuePath, Recovery)
    assert ReceiptPath.read_bytes() == Output.encode("utf-8")
    assert RunFusionTool(QueuePath, Recovery) == Output
    VerifyPhaseJobs(Harness, JsonCodec.loads(Output))
    VerifyUnsafe(QueuePath, Recovery, ReceiptPath, Output.encode("utf-8"))


# a submission intent alone cannot recreate a receipt for uncommitted controller jobs
def VerifyPending(
    QueuePath: str, Recovery: list[str], ReceiptPath: FilePath, DatabasePath: FilePath
) -> None:
    _ = RunFusionTool(QueuePath, Recovery, ExitCode=1)
    assert not ReceiptPath.exists()
    with CloseConnection(SqlCodec.connect(DatabasePath)) as Database:
        assert Database.execute("SELECT COUNT(*) FROM jobs").fetchone() == (0,)


# links and reserved windows aliases cannot replace the exact receipt cell
def VerifyUnsafe(
    QueuePath: str, Recovery: list[str], ReceiptPath: FilePath, Expected: bytes
) -> None:
    LinkedPath = ReceiptPath.with_name("LinkedReceipt.json")
    LinkedPath.hardlink_to(ReceiptPath)
    try:
        _ = RunFusionTool(QueuePath, Recovery, ExitCode=1)
    finally:
        LinkedPath.unlink()
    for AlternateName in (
        f"{ReceiptPath.name}:stream",
        "x:stream",
        "NUL .json",
        f"{ReceiptPath.name}.",
    ):
        AlternatePath = f"{ReceiptPath.parent}\\{AlternateName}"
        _ = RunFusionTool(QueuePath, [*Recovery[:-1], AlternatePath], ExitCode=1)
    assert ReceiptPath.read_bytes() == Expected
    Conflict = b'{"conflict":true}\n'
    _ = ReceiptPath.write_bytes(Conflict)
    _ = RunFusionTool(QueuePath, Recovery, ExitCode=1)
    assert ReceiptPath.read_bytes() == Conflict
