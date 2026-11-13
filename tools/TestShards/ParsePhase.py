from __future__ import annotations

from collections.abc import Mapping

from tools.TestShards.PhaseReport import PhaseReport


def ParsePhase(Fields: Mapping[object, object]) -> PhaseReport:
    TestId = Fields.get("nodeid")
    Phase = Fields.get("when")
    Outcome = Fields.get("outcome")
    Seconds = Fields.get("duration")
    if not isinstance(TestId, str) or not isinstance(Phase, str):
        raise ValueError("report log test entry has no node id or phase")
    if not isinstance(Outcome, str) or not isinstance(Seconds, (int, float)):
        raise ValueError(f"report log entry for {TestId} has invalid results")
    return PhaseReport(TestId, Phase, Outcome, float(Seconds))
