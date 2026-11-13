from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from tools.TestShards.Reuse.Cache.BuildEntry import BuildEntry
from tools.TestShards.Reuse.Cache.CloseDeps import CloseDeps
from tools.TestShards.Reuse.Cache.DepGraph import DepGraph
from tools.TestShards.Reuse.Cache.ReusableOutcomes import KReusableOutcomes
from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex


def MeasureModules(
    Graph: DepGraph,
    TreeInfo: TreeIndex,
    Outcomes: Mapping[str, str],
    Stamp: Mapping[str, str],
) -> tuple[dict[str, dict[str, object]], Counter[str]]:
    Grouped: dict[str, dict[str, str]] = {}
    for TestId, Outcome in Outcomes.items():
        Grouped.setdefault(TestId.split("::", 1)[0], {})[TestId] = Outcome
    Entries: dict[str, dict[str, object]] = {}
    Reasons: Counter[str] = Counter()
    for ModKey, Results in sorted(Grouped.items()):
        if not KReusableOutcomes.issuperset(Results.values()):
            Reasons["had a failed or missing test"] += 1
            continue
        if ModKey not in Graph.Modules:
            Reasons["had no recorded dependencies"] += 1
            continue
        Closure = CloseDeps(Graph, ModKey, TreeInfo.Blobs)
        Entry = BuildEntry(Closure, TreeInfo, Results, Stamp)
        if isinstance(Entry, str):
            Reasons[Entry] += 1
        else:
            Entries[ModKey] = Entry
    return Entries, Reasons
