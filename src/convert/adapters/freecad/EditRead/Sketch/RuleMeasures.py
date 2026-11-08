# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from math import atan2 as ArcTangent, hypot as Hypot, isclose as IsClose, pi as HalfTurn

from convert.adapters.freecad.EditRead.Sketch.RuleOperands import (
    KSketchAngleTol,
    KSketchRuleTol,
    PointDelta,
    RuleCircle,
    RuleLine,
    RuleLineAxis,
    RuleOperand,
    RulePoint,
)
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import SavedRuleRow
from convert.adapters.freecad.Protocol import KRuleValueKindByCode
from convert.adapters.freecad.SketchRuleValue import GetRuleSign
from convert.geometry.Formula.FormulaUnits import GetQuantity
from interchange.enums.EnumValues import ValueKind
from interchange.geometry.models.Sketch import SketchRelation
from interchange.records.RecordParameter import Parameter


# native angle orientation follows the directed line order rather than an unsigned acos
def RuleAngle(First: RuleOperand, Second: RuleOperand) -> float:
    AxisA, _ = RuleLineAxis(RuleLine(First))
    AxisB, _ = RuleLineAxis(RuleLine(Second))
    Angle = ArcTangent(
        AxisA.x * AxisB.y - AxisA.y * AxisB.x,
        AxisA.x * AxisB.x + AxisA.y * AxisB.y,
    )
    if not 0.0 < Angle < HalfTurn:
        raise ValueError(
            "FreeCAD editable sketch angular constraint orientation changed"
        )
    return Angle


# exact edited geometry supplies the independent solver unit measurement
def RuleMeasure(KindValue: str, Operands: tuple[RuleOperand, ...]) -> float:
    if KindValue in ("radius", "diameter") and len(Operands) == 1:
        Radius = RuleCircle(Operands[0]).radius
        return Radius if KindValue == "radius" else Radius * 2.0
    if len(Operands) != 2:
        raise ValueError("FreeCAD editable sketch dimensional operand count changed")
    First, Second = Operands
    if KindValue == "angle":
        return RuleAngle(First, Second)
    if KindValue not in ("distance", "distance_x", "distance_y"):
        raise ValueError("FreeCAD editable sketch dimension kind is unsupported")
    Delta = PointDelta(RulePoint(First), RulePoint(Second))
    if KindValue == "distance_x":
        return Delta.x
    if KindValue == "distance_y":
        return Delta.y
    return Hypot(Delta.x, Delta.y)


# saved values must agree with both geometry and the retained driving parameter when present
def CheckDimRule(
    Relation: SketchRelation,
    Operands: tuple[RuleOperand, ...],
    Saved: SavedRuleRow,
    Parameters: Mapping[str, Parameter],
) -> float | None:
    ParamValue = Parameters.get(Relation.parameter_id or "")
    Expected = KRuleValueKindByCode.get(Saved.CodeValue)
    Quantity = None if ParamValue is None else GetQuantity(ParamValue.value)
    if (
        ParamValue is None
        or Expected is None
        or ParamValue.value.kind != Expected[0]
        or Quantity is None
    ):
        raise ValueError("FreeCAD editable sketch constraint parameter units changed")
    SignValue = GetRuleSign(Relation.kind, Relation.attributes)
    Tolerance = KSketchAngleTol if Expected[0] == ValueKind.KAngle else KSketchRuleTol
    Measured = RuleMeasure(Relation.kind, Operands)
    if SignValue * Saved.Value <= 0.0 or not IsClose(
        Saved.Value, Measured, rel_tol=0.0, abs_tol=Tolerance
    ):
        raise ValueError(
            "FreeCAD editable sketch native constraint value disagrees with geometry"
        )
    if Saved.Driving:
        if not IsClose(
            Saved.Value, SignValue * Quantity[0], rel_tol=0.0, abs_tol=Tolerance
        ):
            raise ValueError(
                "FreeCAD editable sketch driving constraint value disagrees with its parameter"
            )
        return None
    return SignValue * Saved.Value
