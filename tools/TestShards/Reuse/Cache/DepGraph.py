from __future__ import annotations

from typing import NamedTuple

from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps


# dep graph needs an explicit state contract so dependency changes cannot revive stale passing results
class DepGraph(NamedTuple):
    Modules: dict[str, ModuleDeps]
    Links: dict[str, set[str]]
    Listers: dict[str, set[str]]
    Spawners: set[str]
    Pythons: set[str]
    Failed: list[str]
