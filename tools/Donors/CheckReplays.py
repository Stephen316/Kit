from __future__ import annotations

import sys as System
from collections.abc import Sequence

from tools.Donors.ListSources import ListSources
from tools.Donors.ParseArgs import ParseArgs
from tools.Donors.ReportCounts import ReportCounts
from tools.Donors.ScanCounts import ScanCounts


# the run operation needs one orchestration boundary so captured document data cannot become production writer input
def MainRun(ArgValues: Sequence[str] | None = None) -> int:
    NamespaceInfo = ParseArgs(ArgValues)
    PathValues: list[str] = NamespaceInfo.PathValues
    try:
        SourceList = ListSources(PathValues)
        CountMap = ScanCounts(SourceList)
    except (OSError, SyntaxError, UnicodeError) as ErrorInfo:
        print(f"recorded payload check input error: {ErrorInfo}", file=System.stderr)
        return 2
    return ReportCounts(CountMap, len(SourceList))


if __name__ == "__main__":
    raise SystemExit(MainRun())
