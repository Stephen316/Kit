from __future__ import annotations

import builtins as Builtins
import importlib as ImportLib
import os as OsLib
import sys as System
from typing import cast as CastValue

import pytest as Pytest

from tools.TestShards.Reuse.Track.ActiveTrackers import KActiveTrackers
from tools.TestShards.Reuse.Track.BuildAudit import BuildAudit
from tools.TestShards.Reuse.Track.BuildImport import BuildImport
from tools.TestShards.Reuse.Track.BuildModule import BuildModule
from tools.TestShards.Reuse.Track.ForwardCall import ForwardCall
from tools.TestShards.Reuse.Track.TrackState import TrackState


def StartTracking(EarlyConfig: Pytest.Config) -> None:
    KnownArgs = getattr(EarlyConfig, "known_args_namespace", None)
    if not isinstance(getattr(KnownArgs, "TestDeps", None), str) or KActiveTrackers:
        return
    RootText = OsLib.path.realpath(EarlyConfig.rootpath) + OsLib.sep
    ImportFunc = CastValue(ForwardCall, Builtins.__import__)
    ModuleFunc = CastValue(ForwardCall, ImportLib.import_module)
    State = TrackState(RootText, ImportFunc, ModuleFunc)
    KActiveTrackers["State"] = State
    setattr(Builtins, "__import__", BuildImport(State, State.ImportFunc))
    setattr(ImportLib, "import_module", BuildModule(State, State.ModuleFunc))
    System.addaudithook(BuildAudit(State))
