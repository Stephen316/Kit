# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import argparse as ArgParse
from pathlib import Path as FilePath


# dedicated parsing keeps automation flags stable while policy evaluation stays library friendly
def BuildParser() -> ArgParse.ArgumentParser:
    ParserInfo = ArgParse.ArgumentParser(
        description="Validate tracked repository paths and direct directory file counts."
    )
    _ = ParserInfo.add_argument(
        "--root",
        dest="RootPath",
        type=FilePath,
        default=FilePath.cwd(),
        help="repository working tree path",
    )
    _ = ParserInfo.add_argument(
        "--base",
        dest="BaseRef",
        help="base revision for changed destination mode",
    )
    _ = ParserInfo.add_argument(
        "--head",
        dest="HeadRef",
        help="head revision for changed destination mode",
    )
    return ParserInfo
