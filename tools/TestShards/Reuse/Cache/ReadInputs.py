from __future__ import annotations

from pathlib import Path as FilePath

from tools.TestShards.ReadPlan import ReadPlan
from tools.TestShards.ReadReportLog import ReadReportLog
from tools.TestShards.Reuse.Cache.CacheInputs import CacheInputs
from tools.TestShards.Reuse.Cache.FindMissing import FindMissing
from tools.TestShards.Reuse.Cache.LoadCarried import LoadCarried
from tools.TestShards.Reuse.Cache.LoadDeps import LoadDeps
from tools.TestShards.Reuse.Cache.ReadTree import ReadTree
from tools.TestShards.TallyReports import TallyReports


def ReadInputs(
    PlanPath: FilePath,
    ReportsPath: FilePath,
    TreePath: FilePath,
    CarriedPath: FilePath | None,
) -> CacheInputs:
    Plans = ReadPlan(PlanPath)
    LogPaths = sorted(ReportsPath.rglob("*.jsonl"))
    Tally = TallyReports([ReadReportLog(LogPath) for LogPath in LogPaths])
    Outcomes = {
        TestId: Tally.Outcomes.get(TestId, "missing")
        for ShardInfo in Plans
        for TestId in ShardInfo.TestIds
    }
    return CacheInputs(
        Outcomes,
        LoadDeps(sorted(ReportsPath.rglob("Deps-*.json"))),
        ReadTree(TreePath.read_bytes()),
        LoadCarried(CarriedPath),
        FindMissing(LogPaths),
    )
