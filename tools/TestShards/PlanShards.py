from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

from tools.TestShards.AllocateTests import AllocateTests
from tools.TestShards.DescribePlan import DescribePlan
from tools.TestShards.LoadHistory import LoadHistory
from tools.TestShards.PlanArgs import BuildPlanArgs
from tools.TestShards.ReadCollected import ReadCollected
from tools.TestShards.Reuse.Cache.AppendSummary import AppendSummary
from tools.TestShards.Reuse.Select.ChooseReuse import ChooseReuse
from tools.TestShards.Reuse.Select.DescribeReuse import DescribeReuse
from tools.TestShards.Reuse.Select.WriteCarried import WriteCarried
from tools.TestShards.ReusePlan import ReusePlan
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
    Choice = ChooseReuse(
        ArgsInfo.CachePath, ArgsInfo.TreePath, ArgsInfo.MaxAge, TestIds
    )
    Remaining = [TestId for TestId in TestIds if TestId not in Choice.Outcomes]
    Plans = AllocateTests(Remaining, History, MaxTests)
    HistoryCount = sum(TestId in History for TestId in Remaining)
    Seconds = {
        TestId: History[TestId] for TestId in Choice.Outcomes if TestId in History
    }
    Reused = ReusePlan(Choice.Run, Choice.Outcomes, Seconds, len(TestIds))
    WritePlan(ArgsInfo.OutputPath, Plans, (MaxTests, HistoryCount), Reused)
    WriteCarried(ArgsInfo.CarriedPath, Choice.Entries)
    SummaryText = DescribePlan(Plans, MaxTests, HistoryCount) + DescribeReuse(Choice)
    AppendSummary(SummaryText, ArgsInfo.SummaryPath)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
