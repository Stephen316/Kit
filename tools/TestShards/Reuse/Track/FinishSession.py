from __future__ import annotations

import builtins as Builtins
import importlib as ImportLib
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as Pytest

from tools.TestShards.Reuse.Track.ActiveTrackers import KActiveTrackers
from tools.TestShards.Reuse.Track.WriteDeps import WriteDeps


def FinishSession(SessionInfo: Pytest.Session) -> None:
    State = KActiveTrackers.pop("State", None)
    if State is None:
        return
    State.Active = False
    setattr(Builtins, "__import__", State.ImportFunc)
    setattr(ImportLib, "import_module", State.ModuleFunc)
    OutDir = SessionInfo.config.getoption("TestDeps")
    WorkerInput = getattr(SessionInfo.config, "workerinput", None)
    WorkerId = (
        CastValue(dict[str, object], WorkerInput).get("workerid")
        if isinstance(WorkerInput, dict)
        else None
    )
    if isinstance(OutDir, str):
        WriteDeps(
            State, FilePath(OutDir), WorkerId if isinstance(WorkerId, str) else "main"
        )
