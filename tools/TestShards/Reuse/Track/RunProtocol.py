from __future__ import annotations

import os as OsLib
from collections.abc import Generator

import pytest as Pytest

from tools.TestShards.Reuse.Track.ActiveTrackers import KActiveTrackers
from tools.TestShards.Reuse.Track.LocateFile import LocateFile


# the protocol operation needs one orchestration boundary so dependency changes cannot revive stale passing results
def RunProtocol(ItemInfo: Pytest.Item) -> Generator[None, object, object]:
    State = KActiveTrackers.get("State")
    if State is None:
        return (yield)
    State.Current = LocateFile(State.RootText, OsLib.path.abspath(ItemInfo.path))
    try:
        return (yield)
    finally:
        State.Current = None
