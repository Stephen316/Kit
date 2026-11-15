from __future__ import annotations

import os as OsLib
from collections.abc import Generator

import pytest as Pytest

from tools.TestShards.Reuse.Track.ActiveTrackers import KActiveTrackers
from tools.TestShards.Reuse.Track.LocateFile import LocateFile


# the collect module contract needs a shared interpretation so dependency changes cannot revive stale passing results
def CollectModule(Collector: Pytest.Collector) -> Generator[None, object, object]:
    State = KActiveTrackers.get("State")
    if State is None or not isinstance(Collector, Pytest.Module):
        return (yield)
    Previous = State.Current
    State.Current = LocateFile(State.RootText, OsLib.path.abspath(Collector.path))
    try:
        return (yield)
    finally:
        State.Current = Previous
