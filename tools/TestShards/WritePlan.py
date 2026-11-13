from __future__ import annotations

import json as JsonLib
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.TestShards.ShardPlan import ShardPlan


def WritePlan(
    OutputPath: FilePath, Plans: Sequence[ShardPlan], MaxTests: int, HistoryCount: int
) -> None:
    Payload: dict[str, object] = {
        "MaxTests": MaxTests,
        "TestCount": sum(len(ShardInfo.TestIds) for ShardInfo in Plans),
        "HistoryCount": HistoryCount,
        "Shards": [
            {
                "Index": ShardInfo.Index,
                "Estimate": round(ShardInfo.Estimate, 3),
                "TestIds": list(ShardInfo.TestIds),
            }
            for ShardInfo in Plans
        ],
    }
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    _ = OutputPath.write_text(JsonLib.dumps(Payload, indent=1) + "\n", encoding="utf-8")
