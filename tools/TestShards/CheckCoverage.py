from __future__ import annotations

from collections.abc import Sequence

from tools.TestShards.Reuse.Cache.ReusableOutcomes import KReusableOutcomes
from tools.TestShards.ReusePlan import ReusePlan


def CheckCoverage(Planned: Sequence[str], Reused: ReusePlan) -> list[str]:
    Problems: list[str] = []
    Overlap = Reused.Outcomes.keys() & set(Planned)
    if Overlap:
        Problems.append(f"{len(Overlap)} tests are both planned and reused")
    Covered = len(Reused.Outcomes.keys() | set(Planned))
    if Covered != Reused.CollectedCount:
        Problems.append(
            f"the plan covers {Covered} of {Reused.CollectedCount} collected tests"
        )
    Failing = [
        TestId
        for TestId, Outcome in sorted(Reused.Outcomes.items())
        if Outcome not in KReusableOutcomes
    ]
    Problems.extend(f"{TestId} reuses a failed result" for TestId in Failing)
    return Problems
