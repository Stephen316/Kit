from __future__ import annotations

from collections.abc import Sequence
from itertools import chain, zip_longest


def PairExtremes(Ranked: Sequence[int]) -> list[int]:
    HalfCount = (len(Ranked) + 1) // 2
    Pairs = zip_longest(Ranked[:HalfCount], reversed(Ranked[HalfCount:]))
    return [Position for Position in chain.from_iterable(Pairs) if Position is not None]
