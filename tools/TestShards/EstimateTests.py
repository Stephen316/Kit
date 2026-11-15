from __future__ import annotations

import statistics as StatsLib
from collections.abc import Mapping, Sequence

# default weight must remain consistent across callers so every collected case receives exactly one verified outcome
KDefaultWeight = 1.0


# the estimate contract needs a shared interpretation so every collected case receives exactly one verified outcome
def EstimateTests(
    TestIds: Sequence[str], Durations: Mapping[str, float]
) -> list[float]:
    KnownTimes = [Durations[TestId] for TestId in TestIds if TestId in Durations]
    Fallback = StatsLib.median(KnownTimes) if KnownTimes else KDefaultWeight
    return [Durations.get(TestId, Fallback) for TestId in TestIds]
