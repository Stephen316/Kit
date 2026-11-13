from __future__ import annotations

import json as JsonLib
from collections.abc import Mapping, Sequence
from pathlib import Path as FilePath

from tools.TestShards.ReusePlan import ReusePlan
from tools.TestShards.ShardPlan import ShardPlan


def WriteDurations(
    OutputPath: FilePath,
    Plans: Sequence[ShardPlan],
    Durations: Mapping[str, float],
    Reused: ReusePlan,
) -> None:
    Planned = {TestId for ShardInfo in Plans for TestId in ShardInfo.TestIds}
    Measured = {
        TestId: Seconds for TestId, Seconds in Durations.items() if TestId in Planned
    }
    Recorded = {
        TestId: round(Seconds, 4)
        for TestId, Seconds in sorted({**Reused.Seconds, **Measured}.items())
    }
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    Payload = JsonLib.dumps({"Durations": Recorded}, indent=1)
    _ = OutputPath.write_text(Payload + "\n", encoding="utf-8")
