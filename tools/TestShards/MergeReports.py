from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

from tools.TestShards.FindProblems import FindProblems
from tools.TestShards.FormatSummary import FormatSummary
from tools.TestShards.MergeArgs import BuildMergeArgs
from tools.TestShards.ReadPlan import ReadPlan
from tools.TestShards.ReadReuse import ReadReuse
from tools.TestShards.ReadReportLog import ReadReportLog
from tools.TestShards.TallyReports import TallyReports
from tools.TestShards.WriteDurations import WriteDurations


def MainRun(ArgList: list[str] | None = None) -> int:
    ArgsInfo = BuildMergeArgs().parse_args(ArgList)
    ReportsPath: FilePath = ArgsInfo.ReportsPath
    try:
        Plans = ReadPlan(ArgsInfo.PlanPath)
        Reused = ReadReuse(ArgsInfo.PlanPath, Plans)
        LogPaths = sorted(ReportsPath.rglob("*.jsonl")) if ReportsPath.is_dir() else []
        Tally = TallyReports([ReadReportLog(LogPath) for LogPath in LogPaths])
    except (OSError, UnicodeError, ValueError) as ErrorInfo:
        print(f"test shard report input error: {ErrorInfo}", file=System.stderr)
        return 2
    Problems = FindProblems(Plans, Tally, len(LogPaths), Reused)
    WriteDurations(ArgsInfo.OutputPath, Plans, Tally.Durations, Reused)
    SummaryText = FormatSummary(Plans, Tally, Problems, Reused)
    print(SummaryText)
    SummaryPath: FilePath | None = ArgsInfo.SummaryPath
    if SummaryPath is not None:
        with SummaryPath.open("a", encoding="utf-8") as SummaryFile:
            _ = SummaryFile.write(SummaryText)
    for Problem in Problems:
        print(f"::error::{Problem}")
    return 1 if Problems else 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
