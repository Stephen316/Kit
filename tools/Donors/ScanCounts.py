from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.Donors.CountSource import CountSource
from tools.Donors.ShowPath import ShowPath


# the scan counts contract needs a shared interpretation so captured document data cannot become production writer input
def ScanCounts(SourceList: Sequence[FilePath]) -> dict[str, tuple[int, int]]:
    CountMap: dict[str, tuple[int, int]] = {}
    for SourcePath in SourceList:
        SourceText = SourcePath.read_text(encoding="utf-8")
        FieldTotal, CallTotal = CountSource(SourceText, str(SourcePath))
        if FieldTotal or CallTotal:
            CountMap[ShowPath(SourcePath)] = (FieldTotal, CallTotal)
    return CountMap
