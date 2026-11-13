from __future__ import annotations

import argparse as ArgParse
from pathlib import Path as FilePath


def BuildCacheArgs() -> ArgParse.ArgumentParser:
    ParserInfo = ArgParse.ArgumentParser(
        description="Record the dependencies of passing test modules for later plans."
    )
    for FlagText, DestName in (
        ("--plan", "PlanPath"),
        ("--reports", "ReportsPath"),
        ("--tree", "TreePath"),
        ("--output", "OutputPath"),
    ):
        _ = ParserInfo.add_argument(
            FlagText, dest=DestName, type=FilePath, required=True
        )
    _ = ParserInfo.add_argument("--carried", dest="CarriedPath", type=FilePath)
    _ = ParserInfo.add_argument("--run", dest="RunText", required=True)
    _ = ParserInfo.add_argument("--summary", dest="SummaryPath", type=FilePath)
    return ParserInfo
