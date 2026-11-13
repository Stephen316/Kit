from __future__ import annotations

from collections.abc import Sequence

from tools.TestShards.ShardPlan import ShardPlan


def DescribePlan(Plans: Sequence[ShardPlan], MaxTests: int, HistoryCount: int) -> str:
    TestCount = sum(len(ShardInfo.TestIds) for ShardInfo in Plans)
    LineList = [
        "## Test suite plan",
        "",
        f"{TestCount} tests across {len(Plans)} shards with at most {MaxTests} each.",
        f"{HistoryCount} collected tests have recorded durations from an earlier run.",
        "",
        "| Shard | Tests | Estimated seconds |",
        "| ----- | ----- | ----------------- |",
    ]
    LineList.extend(
        f"| {ShardInfo.Index} | {len(ShardInfo.TestIds)} | {ShardInfo.Estimate:.1f} |"
        for ShardInfo in Plans
    )
    return "\n".join(LineList) + "\n"
