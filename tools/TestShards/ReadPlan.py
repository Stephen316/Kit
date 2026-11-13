from __future__ import annotations

import json as JsonLib
from pathlib import Path as FilePath
from typing import cast as CastValue

from tools.TestShards.ParseShard import ParseShard
from tools.TestShards.ShardPlan import ShardPlan


def ReadPlan(PlanPath: FilePath) -> list[ShardPlan]:
    Decoded: object = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))
    ShardList = (
        CastValue(dict[object, object], Decoded).get("Shards")
        if isinstance(Decoded, dict)
        else None
    )
    if not isinstance(ShardList, list) or not ShardList:
        raise ValueError(f"{PlanPath} has no shard list")
    return [ParseShard(Entry) for Entry in CastValue(list[object], ShardList)]
