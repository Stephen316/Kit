from __future__ import annotations

import sys as System
from collections.abc import Mapping

from tools.Donors.ReplayRules import KStandardPath


# the report counts contract needs a shared interpretation so captured document data cannot become production writer input
def ReportCounts(CountMap: Mapping[str, tuple[int, int]], FileTotal: int) -> int:
    for PathText, (FieldTotal, CallTotal) in sorted(CountMap.items()):
        FieldText = f"{FieldTotal} recorded field operations"
        print(f"{PathText}: {FieldText}, {CallTotal} re-emission calls")
    if CountMap:
        CountText = f"recorded payloads found in {len(CountMap)} files"
        print(f"{CountText}; see {KStandardPath}", file=System.stderr)
        return 1
    print(f"no recorded payloads in {FileTotal} files")
    return 0
