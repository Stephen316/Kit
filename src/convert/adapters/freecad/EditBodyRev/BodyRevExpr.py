# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditRev.RevPhaseExpr import RevMeanExpr, RevPhaseExpr


# a reversed native edge uses the opposite sweep angle even if its curve is unchanged
def BodyAngleExpr(
    Extrude: str,
    EdgeName: str,
    Profile: str,
    ProfileLines: tuple[int, ...],
    Reference: str,
    DepthRef: str,
) -> str:
    EdgePath = f"{Extrude}.Shape.{EdgeName}"
    Start = f"{EdgePath}.Vertex1.Point"
    Direction = f"{EdgePath}.Curve.Direction"
    Orient = f"({EdgePath}.Orientation == <<Reversed>> ? -1 : 1)"
    Along = f"({Direction} * {Orient})"
    Point = RevMeanExpr(Profile, ProfileLines)
    Sweep = RevPhaseExpr(Along, Start, Point, Profile, Reference)
    return f"abs({DepthRef}) <= 1e-7 mm ? 0 deg : (abs({Reference}) > 360 deg ? 0 deg : ({Sweep}))"


# a zero depth must invalidate the solid instead of accepting the native default extrusion
def BodyDepthDir(Direction: tuple[float, float, float], DepthRef: str) -> str:
    Components = "; ".join(f"{Value:.17g}" for Value in Direction)
    return f"abs({DepthRef}) > 1e-7 mm ? vector({Components}) : vector(0; 0; 0)"
