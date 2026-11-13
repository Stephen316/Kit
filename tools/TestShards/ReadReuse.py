from __future__ import annotations

import json as JsonLib
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.ReadObject import ReadObject
from tools.TestShards.Reuse.Cache.ReadTexts import ReadTexts
from tools.TestShards.ReusePlan import ReusePlan
from tools.TestShards.ShardPlan import ShardPlan


def ReadReuse(PlanPath: FilePath, Plans: Sequence[ShardPlan]) -> ReusePlan:
    Decoded: object = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))
    Fields = ReadObject(Decoded, PlanPath.name)
    PlannedCount = sum(len(ShardInfo.TestIds) for ShardInfo in Plans)
    CollectedCount = Fields.get("CollectedCount", PlannedCount)
    if not isinstance(CollectedCount, int) or isinstance(CollectedCount, bool):
        raise ValueError(f"{PlanPath} has no integer collected count")
    Section = ReadObject(Fields.get("Reused", {"Run": "", "Outcomes": {}}), "Reused")
    RunText = Section.get("Run")
    if not isinstance(RunText, str):
        raise ValueError(f"{PlanPath} does not name the reused run")
    Seconds = {
        TestId: float(Value)
        for TestId, Value in ReadObject(Section.get("Seconds", {}), "Seconds").items()
        if isinstance(Value, (int, float)) and not isinstance(Value, bool)
    }
    Outcomes = ReadTexts(Section.get("Outcomes"), "Reused outcomes")
    return ReusePlan(RunText, Outcomes, Seconds, CollectedCount)
