from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from tools.TestShards.MergeOutcome import MergeOutcome
from tools.TestShards.ReportTally import ReportTally
from tools.TestShards.ShardLog import ShardLog


def TallyReports(ShardLogs: Sequence[ShardLog]) -> ReportTally:
    Durations: dict[str, float] = {}
    Outcomes: dict[str, str] = {}
    SetupCounts: Counter[str] = Counter()
    for LogInfo in ShardLogs:
        for PhaseInfo in LogInfo.Phases:
            TestId = PhaseInfo.TestId
            Durations[TestId] = Durations.get(TestId, 0.0) + PhaseInfo.Seconds
            Outcomes[TestId] = MergeOutcome(Outcomes.get(TestId), PhaseInfo)
            if PhaseInfo.Phase == "setup":
                SetupCounts[TestId] += 1
    Unfinished = sum(not LogInfo.Finished for LogInfo in ShardLogs)
    return ReportTally(Durations, Outcomes, SetupCounts, Unfinished)
