from __future__ import annotations

from tools.TestShards.PhaseReport import PhaseReport

KOutcomeRanks = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}


def MergeOutcome(Current: str | None, PhaseInfo: PhaseReport) -> str:
    Candidate = PhaseInfo.Outcome
    if Candidate == "failed" and PhaseInfo.Phase != "call":
        Candidate = "error"
    if Current is None or KOutcomeRanks.get(Candidate, 3) > KOutcomeRanks.get(
        Current, 3
    ):
        return Candidate
    return Current
