# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import argparse as Argparse


# explicit modes prevent verification commands from mutating checked in generated files
def ParseArgs() -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="Generate and verify the Agent Skills copy of Kiro steering."
    )
    ModeGroup = ParserInfo.add_mutually_exclusive_group()
    _ = ModeGroup.add_argument(
        "--write",
        action="store_true",
        help="write the Agent Skills copy from .kiro/steering",
    )
    _ = ModeGroup.add_argument(
        "--check",
        action="store_true",
        help="verify the Agent Skills copy without writing (the default)",
    )
    return ParserInfo.parse_args()
