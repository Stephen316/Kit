from __future__ import annotations

from pathlib import Path as FilePath


# the append summary contract needs a shared interpretation so dependency changes cannot revive stale passing results
def AppendSummary(SummaryText: str, SummaryPath: FilePath | None) -> None:
    print(SummaryText)
    if SummaryPath is None:
        return
    with SummaryPath.open("a", encoding="utf-8") as SummaryFile:
        _ = SummaryFile.write(SummaryText)
