from __future__ import annotations

import json as JsonLib
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.TestShards.ReusePlan import ReusePlan
from tools.TestShards.ShardPlan import ShardPlan


def WritePlan(
    OutputPath: FilePath,
    Plans: Sequence[ShardPlan],
    Counts: tuple[int, int],
    Reused: ReusePlan,
) -> None:
    Payload: dict[str, object] = {
        "MaxTests": Counts[0],
        "TestCount": sum(len(ShardInfo.TestIds) for ShardInfo in Plans),
        "CollectedCount": Reused.CollectedCount,
        "HistoryCount": Counts[1],
        "Reused": {
            "Run": Reused.Run,
            "Outcomes": dict(sorted(Reused.Outcomes.items())),
            "Seconds": dict(sorted(Reused.Seconds.items())),
        },
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
