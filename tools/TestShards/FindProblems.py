from __future__ import annotations

from collections.abc import Sequence

from tools.TestShards.CheckCoverage import CheckCoverage
from tools.TestShards.ReportTally import ReportTally
from tools.TestShards.ReusePlan import ReusePlan
from tools.TestShards.ShardPlan import ShardPlan

KListedLimit = 50


def FindProblems(
    Plans: Sequence[ShardPlan], Tally: ReportTally, LogCount: int, Reused: ReusePlan
) -> list[str]:
    Planned = [TestId for ShardInfo in Plans for TestId in ShardInfo.TestIds]
    PlannedSet = set(Planned)
    Executed = set(Tally.SetupCounts)
    Problems = CheckCoverage(Planned, Reused)
    if len(PlannedSet) != len(Planned):
        Problems.append("the plan assigns at least one test to several shards")
    if LogCount != len(Plans):
        Problems.append(f"expected {len(Plans)} shard report logs but found {LogCount}")
    if Tally.Unfinished:
        Problems.append(
            f"{Tally.Unfinished} shard report logs end before session finish"
        )
    Groups = (
        ("never ran", sorted(PlannedSet - Executed)),
        ("ran without being planned", sorted(Executed - PlannedSet)),
        (
            "ran more than once",
            sorted(TestId for TestId in Executed if Tally.SetupCounts[TestId] > 1),
        ),
    )
    for Reason, TestIds in Groups:
        Problems.extend(f"{TestId} {Reason}" for TestId in TestIds[:KListedLimit])
        if len(TestIds) > KListedLimit:
            Problems.append(f"{len(TestIds) - KListedLimit} more tests {Reason}")
    return Problems
