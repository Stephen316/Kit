from __future__ import annotations

import argparse as ArgParse
from pathlib import Path as FilePath


def BuildMergeArgs() -> ArgParse.ArgumentParser:
    ParserInfo = ArgParse.ArgumentParser(
        description="Verify shard report logs against the plan and record durations."
    )
    _ = ParserInfo.add_argument("--plan", dest="PlanPath", type=FilePath, required=True)
    _ = ParserInfo.add_argument(
        "--reports", dest="ReportsPath", type=FilePath, required=True
    )
    _ = ParserInfo.add_argument(
        "--output", dest="OutputPath", type=FilePath, required=True
    )
    _ = ParserInfo.add_argument("--summary", dest="SummaryPath", type=FilePath)
    return ParserInfo
