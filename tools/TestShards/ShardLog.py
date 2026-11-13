from __future__ import annotations

from typing import NamedTuple

from tools.TestShards.PhaseReport import PhaseReport


class ShardLog(NamedTuple):
    Phases: tuple[PhaseReport, ...]
    Finished: bool
