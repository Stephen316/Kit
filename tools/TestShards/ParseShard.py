from __future__ import annotations

from typing import cast as CastValue

from tools.TestShards.ShardPlan import ShardPlan


def ParseShard(Entry: object) -> ShardPlan:
    if not isinstance(Entry, dict):
        raise ValueError("shard plan entry is not an object")
    Fields = CastValue(dict[object, object], Entry)
    Index = Fields.get("Index")
    Estimate = Fields.get("Estimate")
    Members = Fields.get("TestIds")
    if not isinstance(Index, int) or isinstance(Index, bool):
        raise ValueError("shard plan entry has no integer index")
    if not isinstance(Estimate, (int, float)) or not isinstance(Members, list):
        raise ValueError(f"shard {Index} has invalid estimate or test ids")
    TestIds = [
        TestId for TestId in CastValue(list[object], Members) if isinstance(TestId, str)
    ]
    if len(TestIds) != len(CastValue(list[object], Members)):
        raise ValueError(f"shard {Index} lists a test id that is not text")
    return ShardPlan(Index, tuple(TestIds), float(Estimate))
