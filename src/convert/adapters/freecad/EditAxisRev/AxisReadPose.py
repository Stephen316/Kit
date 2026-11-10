# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import degrees as Degrees, isclose as IsClose

from convert.adapters.freecad.EditAxisRev.AxisEndpoints import WorldAxisLine
from convert.adapters.freecad.EditRead.PlaneRev.ExprMatch import IsSamePlaneExpr
from convert.adapters.freecad.EditRead.Revolve.RevControls import CheckRevVector
from convert.adapters.freecad.EditRead.XmlField import (
    EditChild,
    EditFloat,
    OnlyEditChild,
)
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# native expression rewriting may change grouping but must preserve every live dependency
def CheckAxisExpr(Native: NativeObject, Expected: tuple[str, ...]) -> None:
    Engine = EditChild(
        Native, "ExpressionEngine", "App::PropertyExpressionEngine", "ExpressionEngine"
    )
    Expression = OnlyEditChild(Engine, "Expression")
    if (
        Engine.attrib != {"count": "1"}
        or set(Expression.attrib) != {"path", "expression"}
        or Expression.get("path") != "Angle"
        or len(Expression)
        or not any(
            IsSamePlaneExpr(Value, Expression.get("expression", ""))
            for Value in Expected
        )
    ):
        raise ValueError("FreeCAD editable sketch axis angle expression changed")


# the persisted subelement must still point to the sole visible guide edge
def CheckAxisLink(
    Native: NativeObject, AxisName: str, GuideId: int, IsSeed: bool
) -> None:
    LinkValue = EditChild(Native, "AxisLink", "App::PropertyLinkSub", "LinkSub")
    SubValue = OnlyEditChild(LinkValue, "Sub")
    Expected = {"value": "Edge1"}
    if not IsSeed:
        Expected["shadow"] = f";g{GuideId};SKT.Edge1"
    if (
        LinkValue.attrib != {"value": AxisName, "count": "1"}
        or SubValue.attrib != Expected
        or len(SubValue)
    ):
        raise ValueError("FreeCAD editable sketch axis native axis link changed")


# a stale angle or vector cannot replace the independently rebuilt neutral sweep
def CheckAxisPose(
    Native: NativeObject,
    Guide: LineGeometry,
    Frame: Transform,
    Effective: SpaceVector,
    Along: float,
    IsSeed: bool,
) -> None:
    _, EndValue, Direction = WorldAxisLine(Guide, Frame)
    CheckRevVector(Native, "Axis", Direction)
    CheckRevVector(Native, "Base", EndValue)
    if (
        any(
            Native.properties[Field].get("status") != (None if IsSeed else "4")
            for Field in ("Axis", "Base")
        )
        or Native.properties["Angle"].get("status") is not None
    ):
        raise ValueError("FreeCAD editable sketch axis native solver status changed")
    Sense = DotVector(Direction, Effective)
    Actual = EditFloat(
        EditChild(Native, "Angle", "App::PropertyFloatConstraint", "Float"), "value"
    )
    if abs(abs(Sense) - 1.0) > 1e-9 or not IsClose(
        Actual,
        Degrees(Along) * (1.0 if Sense > 0.0 else -1.0),
        abs_tol=1e-9,
        rel_tol=0.0,
    ):
        raise ValueError(
            "FreeCAD editable sketch axis angle disagrees with its live controls"
        )
