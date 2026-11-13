from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime as DateTime

from tools.TestShards.Reuse.Cache.TreeIndex import TreeIndex
from tools.TestShards.Reuse.Select.CacheData import CacheData
from tools.TestShards.Reuse.Select.MatchEntry import MatchEntry
from tools.TestShards.Reuse.Select.ReuseChoice import ReuseChoice


def SelectReuse(
    TestIds: Sequence[str], Cache: CacheData, TreeInfo: TreeIndex, Oldest: DateTime
) -> ReuseChoice:
    Grouped: dict[str, list[str]] = {}
    for TestId in TestIds:
        Grouped.setdefault(TestId.split("::", 1)[0], []).append(TestId)
    Entries: dict[str, dict[str, object]] = {}
    Outcomes: dict[str, str] = {}
    for ModKey, Members in Grouped.items():
        Entry = Cache.Modules.get(ModKey)
        if Entry is None:
            continue
        Results = MatchEntry(ModKey, Entry, Members, TreeInfo, Oldest)
        if Results is not None:
            Entries[ModKey] = Entry
            Outcomes.update(Results)
    return ReuseChoice(Cache.Run, Outcomes, Entries, "")
