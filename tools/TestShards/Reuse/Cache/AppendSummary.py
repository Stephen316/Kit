from __future__ import annotations

from pathlib import Path as FilePath


def AppendSummary(SummaryText: str, SummaryPath: FilePath | None) -> None:
    print(SummaryText)
    if SummaryPath is None:
        return
    with SummaryPath.open("a", encoding="utf-8") as SummaryFile:
        _ = SummaryFile.write(SummaryText)
