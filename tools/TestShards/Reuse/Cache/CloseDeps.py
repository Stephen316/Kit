from __future__ import annotations

from collections.abc import Mapping

from tools.TestShards.Reuse.Cache.DepGraph import DepGraph
from tools.TestShards.Reuse.Cache.ListConftests import ListConftests
from tools.TestShards.Reuse.Track.ModuleDeps import ModuleDeps


def CloseDeps(Graph: DepGraph, ModKey: str, Blobs: Mapping[str, str]) -> ModuleDeps:
    Record = Graph.Modules.get(ModKey, ModuleDeps())
    Closure = ModuleDeps(set(), set(Record.Folders), Record.Opaque)
    Pending = [ModKey, *Record.Files, *ListConftests(ModKey, Blobs)]
    while Pending:
        PathText = Pending.pop()
        if PathText in Closure.Files:
            continue
        Closure.Files.add(PathText)
        Closure.Folders.update(Graph.Listers.get(PathText, ()))
        Closure.Opaque = Closure.Opaque or PathText in Graph.Spawners
        Pending.extend(Graph.Links.get(PathText, ()))
    return Closure
