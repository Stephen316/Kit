from __future__ import annotations

from typing import NamedTuple

from tools.TestShards.PhaseReport import PhaseReport


# shard log needs an explicit state contract so every collected case receives exactly one verified outcome
class ShardLog(NamedTuple):
    Phases: tuple[PhaseReport, ...]
    Finished: bool
