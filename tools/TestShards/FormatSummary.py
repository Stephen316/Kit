from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from tools.TestShards.ReportTally import ReportTally
from tools.TestShards.ShardPlan import ShardPlan


def FormatSummary(
    Plans: Sequence[ShardPlan], Tally: ReportTally, Problems: Sequence[str]
) -> str:
    Totals = Counter(Tally.Outcomes.values())
    Verdict = "failed" if Problems else "passed"
    LineList = [
        "## Test suite report",
        "",
        f"Completeness verification {Verdict} for {len(Tally.SetupCounts)} executed tests.",
        ", ".join(f"{Count} {Outcome}" for Outcome, Count in sorted(Totals.items())),
        "",
        "| Shard | Tests | Estimated seconds | Measured seconds |",
        "| ----- | ----- | ----------------- | ---------------- |",
    ]
    for ShardInfo in Plans:
        Measured = sum(Tally.Durations.get(TestId, 0.0) for TestId in ShardInfo.TestIds)
        CellList = (ShardInfo.Index, len(ShardInfo.TestIds), ShardInfo.Estimate)
        LineList.append("| {} | {} | {:.1f} | {:.1f} |".format(*CellList, Measured))
    LineList.extend(f"- {Problem}" for Problem in Problems)
    return "\n".join(LineList) + "\n"
