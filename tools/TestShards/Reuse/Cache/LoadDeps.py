from __future__ import annotations

import json as JsonLib
from collections.abc import Iterable
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.DepGraph import DepGraph
from tools.TestShards.Reuse.Cache.MergeDepsMut import MergeDepsMut
from tools.TestShards.Reuse.Cache.ReadObject import ReadObject


# the deps operation needs a distinct decoding boundary so dependency changes cannot revive stale passing results
def LoadDeps(DepPaths: Iterable[FilePath]) -> DepGraph:
    Graph = DepGraph({}, {}, {}, set(), set(), [])
    for DepPath in DepPaths:
        Decoded: object = JsonLib.loads(DepPath.read_text(encoding="utf-8"))
        MergeDepsMut(Graph, ReadObject(Decoded, DepPath.name))
    return Graph
