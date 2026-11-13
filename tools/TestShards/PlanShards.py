from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

from tools.TestShards.AllocateTests import AllocateTests
from tools.TestShards.DescribePlan import DescribePlan
from tools.TestShards.LoadHistory import LoadHistory
from tools.TestShards.PlanArgs import BuildPlanArgs
from tools.TestShards.ReadCollected import ReadCollected
from tools.TestShards.WritePlan import WritePlan


def MainRun(ArgList: list[str] | None = None) -> int:
    ParserInfo = BuildPlanArgs()
    ArgsInfo = ParserInfo.parse_args(ArgList)
    MaxTests: int = ArgsInfo.MaxTests
    if MaxTests < 1:
        ParserInfo.error("--max-tests must be at least 1")
    try:
        CollectedPath: FilePath = ArgsInfo.CollectedPath
        TestIds = ReadCollected(CollectedPath.read_text(encoding="utf-8"))
        History = LoadHistory(ArgsInfo.HistoryPath)
    except (OSError, UnicodeError, ValueError) as ErrorInfo:
        print(f"test shard planning input error: {ErrorInfo}", file=System.stderr)
        return 2
    Plans = AllocateTests(TestIds, History, MaxTests)
    HistoryCount = sum(TestId in History for TestId in TestIds)
    WritePlan(ArgsInfo.OutputPath, Plans, MaxTests, HistoryCount)
    SummaryText = DescribePlan(Plans, MaxTests, HistoryCount)
    print(SummaryText)
    SummaryPath: FilePath | None = ArgsInfo.SummaryPath
    if SummaryPath is not None:
        with SummaryPath.open("a", encoding="utf-8") as SummaryFile:
            _ = SummaryFile.write(SummaryText)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
