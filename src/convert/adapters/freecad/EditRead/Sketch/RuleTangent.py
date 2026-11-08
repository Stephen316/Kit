# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot

from convert.adapters.freecad.EditRead.Sketch.RuleOperands import (
    KSketchRuleTol,
    PointDelta,
    RuleCircle,
    RuleLine,
    RuleLineLocal,
    RuleOperand,
)
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry


# tangency direction branches must persist instead of flipping the source solution
def TangentBranch(Operands: tuple[RuleOperand, ...]) -> int:
    if len(Operands) != 2:
        raise ValueError("FreeCAD editable sketch tangent operands changed")
    First, Second = Operands
    if isinstance(First.Geometry, CircleGeometry) and isinstance(
        Second.Geometry, CircleGeometry
    ):
        CircleA, CircleB = RuleCircle(First), RuleCircle(Second)
        Delta = PointDelta(CircleA.center, CircleB.center)
        Distance = Hypot(Delta.x, Delta.y)
        SumValue = CircleA.radius + CircleB.radius
        Difference = CircleA.radius - CircleB.radius
        if abs(Distance - SumValue) <= KSketchRuleTol:
            return 1
        if (
            Distance > KSketchRuleTol
            and abs(Distance - abs(Difference)) <= KSketchRuleTol
        ):
            return 2 if Difference > 0.0 else -2
    else:
        LineValue, CircleValue = (
            (First, Second)
            if isinstance(First.Geometry, LineGeometry)
            else (Second, First)
        )
        Circle = RuleCircle(CircleValue)
        Along, Offset, Length = RuleLineLocal(Circle.center, RuleLine(LineValue))
        if (
            -KSketchRuleTol <= Along <= Length + KSketchRuleTol
            and abs(abs(Offset) - Circle.radius) <= KSketchRuleTol
        ):
            return 1 if Offset > 0.0 else -1
    raise ValueError("FreeCAD editable sketch tangent constraint residual changed")
