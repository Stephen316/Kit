# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Literal

from convert.adapters.freecad.EditRev.RevPhaseExpr import RevMeanExpr, RevPhaseExpr


# native positive sweep follows the half plane currently occupied by the profile
def AxisAngleExpr(
    AxisSketch: str,
    AxisIndex: int,
    Profile: str,
    ProfileLines: tuple[int, ...],
    Reference: str,
    MeanStyle: Literal["world", "legacy", "saved"] = "world",
) -> str:
    Guide = f"{AxisSketch}.Geometry[{AxisIndex}]"
    Start = f"({AxisSketch}.Placement * {Guide}.StartPoint)"
    EndValue = f"({AxisSketch}.Placement * {Guide}.EndPoint)"
    Along = f"({EndValue} - {Start})"
    Point = RevMeanExpr(Profile, ProfileLines, MeanStyle)
    return RevPhaseExpr(Along, Start, Point, Profile, Reference)
