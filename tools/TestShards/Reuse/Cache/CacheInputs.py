from __future__ import annotations

from typing import NamedTuple

from tools.TestShards.Reuse.Cache.DepGraph import DepGraph
from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex


class CacheInputs(NamedTuple):
    Outcomes: dict[str, str]
    Graph: DepGraph
    TreeInfo: TreeIndex
    Carried: dict[str, dict[str, object]]
    Missing: list[str]
