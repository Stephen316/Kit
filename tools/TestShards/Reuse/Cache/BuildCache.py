from __future__ import annotations

import sys as System

from tools.TestShards.Reuse.Cache.AppendSummary import AppendSummary
from tools.TestShards.Reuse.Cache.CacheArgs import BuildCacheArgs
from tools.TestShards.Reuse.Cache.ReadInputs import ReadInputs
from tools.TestShards.Reuse.Cache.WriteCache import WriteCache


def MainRun(ArgList: list[str] | None = None) -> int:
    ArgsInfo = BuildCacheArgs().parse_args(ArgList)
    try:
        Inputs = ReadInputs(
            ArgsInfo.PlanPath,
            ArgsInfo.ReportsPath,
            ArgsInfo.TreePath,
            ArgsInfo.CarriedPath,
        )
    except (OSError, UnicodeError, ValueError) as ErrorInfo:
        print(f"test cache input error: {ErrorInfo}", file=System.stderr)
        return 2
    if Inputs.Missing or Inputs.Graph.Failed or len(Inputs.Graph.Pythons) != 1:
        Problems = [f"- missing {PathText}" for PathText in Inputs.Missing]
        Problems.extend(
            f"- tracking failed in {Worker}" for Worker in Inputs.Graph.Failed
        )
        Problems.append(f"- Python versions: {sorted(Inputs.Graph.Pythons)}")
        Header = "## Test cache\n\nNo test cache was recorded because the dependency records are incomplete.\n"
        AppendSummary(Header + "\n".join(Problems) + "\n", ArgsInfo.SummaryPath)
        return 0
    SummaryText = WriteCache(Inputs, ArgsInfo.RunText, ArgsInfo.OutputPath)
    AppendSummary(SummaryText, ArgsInfo.SummaryPath)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
