# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import runpy as ScriptRunner
import sys as System
from collections.abc import Callable
from typing import cast as CastValue

import pytest as Pytest

from tests.Research.Applications.DispatchHost import KRepoRoot


# the auditor consumes retained windows identities even on a different host platform
def CheckFiletime() -> None:
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/AuditFusionPhases.py"
    SearchPath = System.path[:]
    try:
        System.path.insert(0, str(ScriptPath.parent))
        Scope = ScriptRunner.run_path(str(ScriptPath))
    finally:
        System.path[:] = SearchPath
    AuditPhase = CastValue(
        Callable[[dict[str, object], dict[str, object]], dict[str, object]],
        Scope["phase_process"],
    )
    StartTick = 133485408000000001
    Process = {
        "pid": 427,
        "started": f"windows:{StartTick}",
        "start_unix_seconds": StartTick // 10_000_000 - 11_644_473_600,
    }
    Dispatch: dict[str, object] = {
        "host": {"pid": Process["pid"], "started": Process["started"]},
        "reason": "pinned Fusion discovery phase completed",
        "proof": {"fusion_version": "2706.1.17"},
    }
    assert AuditPhase(Dispatch, {"process": Process}) == Process
    Shifted: dict[str, object] = {**Process, "started": f"windows:{StartTick + 1}"}
    Trimmed: dict[str, object] = {
        KeyName: Process[KeyName] for KeyName in ("pid", "start_unix_seconds")
    }
    for Invalid in (Shifted, Trimmed):
        with Pytest.raises(ValueError, match="process FILETIME differs"):
            _ = AuditPhase(Dispatch, {"process": Invalid})
    VerifyFixture(AuditPhase, Dispatch, Trimmed, Shifted)


# only the original explicitly nonnative transport records may omit their tick token
def VerifyFixture(
    AuditPhase: Callable[[dict[str, object], dict[str, object]], dict[str, object]],
    Dispatch: dict[str, object],
    Trimmed: dict[str, object],
    Shifted: dict[str, object],
) -> None:
    Fixture = {"fixture_only": True, "fusion_version": "fixture build"}
    Transport = {
        **Dispatch,
        "reason": "fixture restart transport only",
        "proof": Fixture,
    }
    assert AuditPhase(Transport, {**Fixture, "process": Trimmed}) == Trimmed
    with Pytest.raises(ValueError, match="process FILETIME differs"):
        _ = AuditPhase(Transport, {**Fixture, "process": Shifted})
    with Pytest.raises(ValueError, match="fixture markers differ"):
        _ = AuditPhase(
            Transport, {"process": Trimmed, "fusion_version": "fixture build"}
        )
    with Pytest.raises(ValueError, match="fixture markers differ"):
        _ = AuditPhase(Dispatch, {**Fixture, "process": Trimmed})
    with Pytest.raises(ValueError, match="process FILETIME differs"):
        _ = AuditPhase(
            {**Transport, "reason": "native"}, {**Fixture, "process": Trimmed}
        )
