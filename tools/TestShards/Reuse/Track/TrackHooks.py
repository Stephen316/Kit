from __future__ import annotations

import pytest as Pytest

from tools.TestShards.Reuse.Track.AddOptions import AddOptions
from tools.TestShards.Reuse.Track.BindHookMut import BindHookMut
from tools.TestShards.Reuse.Track.CollectModule import CollectModule
from tools.TestShards.Reuse.Track.FinishSession import FinishSession
from tools.TestShards.Reuse.Track.RunProtocol import RunProtocol
from tools.TestShards.Reuse.Track.StartTracking import StartTracking

KHookSpecs: dict[str, tuple[object, tuple[str, ...]]] = {
    "pytest_addoption": (AddOptions, ("parser",)),
    "pytest_load_initial_conftests": (
        Pytest.hookimpl(tryfirst=True)(StartTracking),
        ("early_config",),
    ),
    "pytest_make_collect_report": (
        Pytest.hookimpl(wrapper=True)(CollectModule),
        ("collector",),
    ),
    "pytest_runtest_protocol": (
        Pytest.hookimpl(wrapper=True)(RunProtocol),
        ("item",),
    ),
    "pytest_sessionfinish": (FinishSession, ("session",)),
}

globals().update(
    {HookName: BindHookMut(*HookSpec) for HookName, HookSpec in KHookSpecs.items()}
)
