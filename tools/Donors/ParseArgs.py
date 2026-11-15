from __future__ import annotations

import argparse as Argparse
from collections.abc import Sequence


# the args operation needs a distinct decoding boundary so captured document data cannot become production writer input
def ParseArgs(ArgValues: Sequence[str] | None = None) -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="reject recorded payload programs in production code"
    )
    _ = ParserInfo.add_argument("PathValues", metavar="PATH", nargs="+")
    return ParserInfo.parse_args(ArgValues)
