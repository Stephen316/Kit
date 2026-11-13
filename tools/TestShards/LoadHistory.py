from __future__ import annotations

import json as JsonLib
import math as MathLib
from pathlib import Path as FilePath
from typing import cast as CastValue


def LoadHistory(HistoryPath: FilePath | None) -> dict[str, float]:
    if HistoryPath is None or not HistoryPath.is_file():
        return {}
    Decoded: object = JsonLib.loads(HistoryPath.read_text(encoding="utf-8"))
    Section = (
        CastValue(dict[object, object], Decoded).get("Durations")
        if isinstance(Decoded, dict)
        else None
    )
    if not isinstance(Section, dict):
        raise ValueError(f"{HistoryPath} has no durations object")
    Durations: dict[str, float] = {}
    for TestId, Seconds in CastValue(dict[object, object], Section).items():
        if not isinstance(TestId, str) or isinstance(Seconds, bool):
            continue
        if isinstance(Seconds, (int, float)) and MathLib.isfinite(Seconds):
            Durations[TestId] = max(float(Seconds), 0.0)
    return Durations
