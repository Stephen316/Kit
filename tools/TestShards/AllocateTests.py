from __future__ import annotations

import heapq as HeapQueue
import math as MathLib
from collections.abc import Mapping, Sequence

from tools.TestShards.EstimateTests import EstimateTests
from tools.TestShards.PairExtremes import PairExtremes
from tools.TestShards.ShardPlan import ShardPlan


def AllocateTests(
    TestIds: Sequence[str], Durations: Mapping[str, float], MaxTests: int
) -> list[ShardPlan]:
    ShardCount = MathLib.ceil(len(TestIds) / MaxTests)
    Weights = EstimateTests(TestIds, Durations)
    Members: dict[int, list[int]] = {ShardPos: [] for ShardPos in range(ShardCount)}
    OpenSlots = [(0.0, 0, ShardPos) for ShardPos in range(ShardCount)]
    Ordered = sorted((-Weight, Position) for Position, Weight in enumerate(Weights))
    for NegWeight, Position in Ordered:
        LoadSecs, Count, ShardPos = HeapQueue.heappop(OpenSlots)
        Members[ShardPos].append(Position)
        if Count + 1 < MaxTests:
            HeapQueue.heappush(OpenSlots, (LoadSecs - NegWeight, Count + 1, ShardPos))
    return [
        ShardPlan(
            ShardPos + 1,
            tuple(TestIds[Position] for Position in PairExtremes(Positions)),
            sum(Weights[Position] for Position in Positions),
        )
        for ShardPos, Positions in Members.items()
    ]
