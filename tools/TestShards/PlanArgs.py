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
    return ParserInfo
