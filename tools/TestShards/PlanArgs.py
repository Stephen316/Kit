from __future__ import annotations

import argparse as ArgParse
from pathlib import Path as FilePath


def BuildPlanArgs() -> ArgParse.ArgumentParser:
    ParserInfo = ArgParse.ArgumentParser(
        description="Allocate collected pytest node ids to capped runtime shards."
    )
    _ = ParserInfo.add_argument(
        "--collected", dest="CollectedPath", type=FilePath, required=True
    )
    _ = ParserInfo.add_argument("--history", dest="HistoryPath", type=FilePath)
    _ = ParserInfo.add_argument("--max-tests", dest="MaxTests", type=int, default=300)
    _ = ParserInfo.add_argument(
        "--output", dest="OutputPath", type=FilePath, required=True
    )
    _ = ParserInfo.add_argument("--summary", dest="SummaryPath", type=FilePath)
    _ = ParserInfo.add_argument("--cache", dest="CachePath", type=FilePath)
    _ = ParserInfo.add_argument("--tree", dest="TreePath", type=FilePath)
    _ = ParserInfo.add_argument("--carried", dest="CarriedPath", type=FilePath)
    _ = ParserInfo.add_argument(
        "--max-age-days", dest="MaxAge", type=float, default=7.0
    )
    return ParserInfo
