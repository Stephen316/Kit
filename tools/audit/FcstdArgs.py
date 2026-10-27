# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import argparse as Argparse
from pathlib import Path as FilePath

from tools.audit.FcstdContext import KRepositoryRoot


# explicit arguments keep recursive scope output mode and failure policy reviewable
def ParseArguments() -> Argparse.Namespace:
    ParserData = Argparse.ArgumentParser(
        description=(
            "Audit FCStd files through the CAD-free first-principles SOLIDWORKS "
            "writer. No CAD application or vendor automation is launched."
        )
    )
    _ = ParserData.add_argument(
        "roots",
        nargs="*",
        type=FilePath,
        default=(KRepositoryRoot,),
        help="file or directory roots to scan recursively",
    )
    _ = ParserData.add_argument(
        "--json",
        action="store_true",
        help="emit the complete machine-readable audit instead of one row per file",
    )
    _ = ParserData.add_argument(
        "--require-vendor-loadable",
        action="store_true",
        help="return a non-zero status unless every discovered FCStd is vendor-loadable",
    )
    _ = ParserData.add_argument(
        "--worker-source", type=FilePath, help=Argparse.SUPPRESS
    )
    _ = ParserData.add_argument(
        "--worker-output", type=FilePath, help=Argparse.SUPPRESS
    )
    _ = ParserData.add_argument("--worker-index", type=int, help=Argparse.SUPPRESS)
    return ParserData.parse_args()
