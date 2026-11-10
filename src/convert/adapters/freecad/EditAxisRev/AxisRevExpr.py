# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
