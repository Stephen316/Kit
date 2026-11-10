# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import degrees as Degrees, isclose as IsClose

from convert.adapters.freecad.EditAxisRev.AxisReadPose import CheckAxisExpr
from convert.adapters.freecad.EditBodyRev.BodyReadGraph import BodyGraph
from convert.adapters.freecad.EditBodyRev.BodyRevExpr import BodyDepthDir
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditBodyRev.PrismOrder import PrismOrder
from convert.adapters.freecad.EditRead.PlaneRev.ExprMatch import IsSamePlaneExpr
from convert.adapters.freecad.EditRead.Revolve.RevControls import CheckRevVector
from convert.adapters.freecad.EditRead.XmlField import (
    EditChild,
    EditFloat,
    OnlyEditChild,
)
from convert.geometry.Revolve.SweepVector import DotVector


# legacy exports used a fixed normal which remains admissible when its saved vector agrees
def CheckBodyExprs(Graph: BodyGraph, PlanValue: BodyRevPlan, DepthRef: str) -> None:
    RevExpr = Graph.Template[Graph.Revolve.name].properties["ExpressionEngine"][0][0]
    CheckAxisExpr(Graph.Revolve, (RevExpr.attrib["expression"],))
    Engine = EditChild(
        Graph.Seed,
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
    )
    if len(Engine) != 2 or Engine.attrib != {"count": "2"}:
        raise ValueError(
            "FreeCAD editable body axis extrusion expression inventory changed"
        )
    Source = PlanValue.Extrude.Direction
    Direction = (Source.x, Source.y, Source.z)
    Directions = (
        BodyDepthDir(Direction, DepthRef, Graph.Source.name),
        BodyDepthDir(Direction, DepthRef),
    )
    for NodeValue, PathValue, Candidates in zip(
        Engine, ("Dir", "LengthFwd"), (Directions, (DepthRef,)), strict=True
    ):
        if (
            NodeValue.tag != "Expression"
            or len(NodeValue)
            or set(NodeValue.attrib) != {"path", "expression"}
            or NodeValue.get("path") != PathValue
            or not any(
                IsSamePlaneExpr(Value, NodeValue.get("expression", ""))
                for Value in Candidates
            )
        ):
            raise ValueError("FreeCAD editable body axis extrusion expression changed")


# native public and persistent link names must both resolve the exact source edge
def CheckBodyLinks(Graph: BodyGraph, EdgeName: str, Shadow: str) -> None:
    RevLink = EditChild(Graph.Revolve, "AxisLink", "App::PropertyLinkSub", "LinkSub")
    SubValue = OnlyEditChild(RevLink, "Sub")
    Expected = {"value": EdgeName}
    PickAttrs = {"obj": Graph.Seed.name, "sub": EdgeName}
    if Shadow:
        Expected["shadow"] = Shadow
        PickAttrs["shadow"] = Shadow
    PickLinks = EditChild(
        Graph.Pick, "Selection", "App::PropertyLinkSubList", "LinkSubList"
    )
    Original = Graph.Template[Graph.Pick.name].properties["Selection"][0]
    if (
        RevLink.attrib != {"value": Graph.Seed.name, "count": "1"}
        or Graph.Revolve.properties["AxisLink"].get("status") is not None
        or SubValue.attrib != Expected
        or len(SubValue)
        or PickLinks.attrib != {"count": "2"}
        or len(PickLinks) != 2
        or any(NodeValue.tag != "Link" or len(NodeValue) for NodeValue in PickLinks)
        or PickLinks[0].attrib != Original[0].attrib
        or PickLinks[1].attrib != PickAttrs
        or Graph.Template[Graph.Revolve.name].properties["AxisLink"][0][0].get("value")
        != EdgeName
    ):
        raise ValueError("FreeCAD editable body axis native edge link changed")


# the saved angle must preserve the neutral phase even when the native rim direction reverses
def CheckBodyPose(
    Graph: BodyGraph,
    Order: PrismOrder,
    PlanValue: BodyRevPlan,
    Along: float,
    IsSeed: bool,
) -> None:
    Native = Graph.Revolve
    CheckRevVector(Native, "Axis", Order.Axis)
    CheckRevVector(Native, "Base", Order.Base)
    if (
        any(
            Native.properties[Field].get("status") != (None if IsSeed else "4")
            for Field in ("Axis", "Base")
        )
        or Native.properties["Angle"].get("status") is not None
    ):
        raise ValueError("FreeCAD editable body axis native solver status changed")
    Actual = EditFloat(
        EditChild(Native, "Angle", "App::PropertyFloatConstraint", "Float"), "value"
    )
    Alignment = DotVector(Order.Axis, PlanValue.Revolve.AxisDirection)
    Expected = Degrees(Along) * (1.0 if Alignment > 0.0 else -1.0)
    if abs(abs(Alignment) - 1.0) > 1e-9 or not IsClose(
        Actual, Expected, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError(
            "FreeCAD editable body axis angle disagrees with its live controls"
        )
