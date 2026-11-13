from __future__ import annotations

import platform as Platform
from collections.abc import Sequence
from datetime import UTC
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.ComputeGuard import ComputeGuard
from tools.TestShards.Reuse.Cache.ReadTree import ReadTree
from tools.TestShards.Reuse.Select.LoadCache import LoadCache
from tools.TestShards.Reuse.Select.ReuseChoice import ReuseChoice
from tools.TestShards.Reuse.Select.SelectReuse import SelectReuse

KGuardReason = (
    "the Python version, dependencies, pytest configuration, or test tooling changed"
)


def ChooseReuse(
    CachePath: FilePath | None,
    TreePath: FilePath | None,
    MaxAge: float,
    TestIds: Sequence[str],
) -> ReuseChoice:
    if CachePath is None or TreePath is None or not CachePath.is_file():
        return ReuseChoice("", {}, {}, "no earlier merge-group test cache is available")
    try:
        Cache = LoadCache(CachePath)
        TreeInfo = ReadTree(TreePath.read_bytes())
        if Cache.Guard != ComputeGuard(TreeInfo.Blobs, Platform.python_version()):
            return ReuseChoice(Cache.Run, {}, {}, KGuardReason)
        Oldest = DateTime.now(UTC) - TimeDelta(days=MaxAge)
        Choice = SelectReuse(TestIds, Cache, TreeInfo, Oldest)
        if len(Choice.Outcomes) == len(TestIds):
            return ReuseChoice(Cache.Run, {}, {}, "every collected test was reusable")
        return Choice
    except (OSError, TypeError, UnicodeError, ValueError) as ErrorInfo:
        return ReuseChoice("", {}, {}, f"the test cache cannot be read: {ErrorInfo}")
