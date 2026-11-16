# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadRectDims import ReadRectDims
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


# the selected constrained profile must prove its exact additions before sharing ordinary strict guards
def ReadRectRules(
    Graph: NativeGraph, Context: ExtrudeContext
) -> RectSketchProof | None:
    Geometric = Graph.ByClass("SketchGeomConstraint")
    Linear = Graph.ByClass("FusionSketchLinearDim")
    if not Geometric and not Linear:
        return None
    if len(Geometric) != 5 or len(Linear) != 2:
        raise ValueError(
            "Native constrained rectangle requires five rules and two dimensions"
        )
    CheckRectUnits(Graph)
    Rules = LinkedNodes(Graph, Context.Sketch, "constraints")
    Dimensions = LinkedNodes(Graph, Context.Sketch, "dimensions")
    SameNodes(Rules, Geometric)
    SameNodes(Dimensions, Linear)
    Lines = OrderLines(Graph, Graph.ByClass("Line3D"))
    AnchorRule, Anchor, Origin = ReadRectAnchor(Graph, Context, Rules, Lines)
    AxisRules = ReadRectAxes(Graph, Context, Rules, AnchorRule, Lines)
    Bindings, Params, SizeRules = ReadRectDims(
        Graph, Context, Dimensions, Lines, Anchor
    )
    AnchorRelation = SketchRelation(
        AnchorRule.Identity,
        ConstraintKind.KCoincident,
        (ConstraintRef(Anchor.Identity), ConstraintRef(Origin.Identity)),
    )
    return RectSketchProof(
        Rules,
        Dimensions,
        Bindings,
        Params,
        Anchor,
        Origin,
        (*AxisRules, AnchorRelation, *SizeRules),
    )


# the qualified source family records a millimeter choice in its active unit system
def CheckRectUnits(Graph: NativeGraph) -> None:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Units = ResolveField(Graph, Settings, "activeUnitSystem", "UnitSystem")
    Lengths = tuple(
        Choice
        for Choice in LinkedNodes(Graph, Units, "children")
        if Choice.ClassName == "UnitSystemChoiceById"
        and Choice.Fields["id"] == "ModelingLength"
    )
    if len(Lengths) != 1:
        raise ValueError(
            "Native constrained rectangle requires one modeling length setting"
        )
    RequireFields(
        Lengths[0], {"unitString": "millimeter", "rParent": LocalRef(Units.ObjectId)}
    )


# the free corner and the fixed origin have distinct identities and share only the proved coincidence
def ReadRectAnchor(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Rules: tuple[NativeNode, ...],
    Lines: tuple[NativeNode, ...],
) -> tuple[NativeNode, NativeNode, NativeNode]:
    Anchors = tuple(
        RuleNode for RuleNode in Rules if RuleNode.Fields["constraintType"] == 1
    )
    if len(Anchors) != 1:
        raise ValueError(
            "Native constrained rectangle requires one distinct origin coincidence"
        )
    RuleNode = Anchors[0]
    Targets = LinkedNodes(Graph, RuleNode, "geometries")
    if len(Targets) != 2 or any(
        NodeValue.ClassName != "Point3D" for NodeValue in Targets
    ):
        raise ValueError(
            "Native rectangle origin coincidence requires two point operands"
        )
    Anchor, Origin = Targets
    Endpoints = tuple(
        ResolveField(Graph, LineNode, "rStartPoint", "Point3D") for LineNode in Lines
    )
    SameNodes((*Endpoints, Origin), Graph.ByClass("Point3D"))
    if (
        Anchor not in Endpoints
        or Origin in Endpoints
        or any(
            Graph.Resolve(Point.Fields["rParent"]) != Context.Sketch
            for Point in Targets
        )
        or PointCoords(Anchor.Fields["point"]) != (0.0, 0.0, 0.0)
        or PointCoords(Origin.Fields["point"]) != (0.0, 0.0, 0.0)
    ):
        raise ValueError(
            "Native rectangle origin does not bind its distinct anchored corner"
        )
    RequireFields(Anchor, {"isOrigin": False, "isFixed": False})
    RequireFields(Origin, {"isOrigin": True, "isFixed": True})
    CheckRuleFrame(Graph, Context, RuleNode, (Origin, Anchor))
    return RuleNode, Anchor, Origin


# every exact line needs its own matching horizontal or vertical saved rule
def ReadRectAxes(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Rules: tuple[NativeNode, ...],
    AnchorRule: NativeNode,
    Lines: tuple[NativeNode, ...],
) -> tuple[SketchRelation, ...]:
    ByLine: dict[str, SketchRelation] = {}
    for RuleNode in Rules:
        if RuleNode == AnchorRule:
            continue
        Targets = LinkedNodes(Graph, RuleNode, "geometries")
        if (
            len(Targets) != 1
            or Targets[0] not in Lines
            or Targets[0].Identity in ByLine
        ):
            raise ValueError(
                "Native rectangle axis rules must identify four distinct sides"
            )
        LineNode = Targets[0]
        KindValue, CodeValue = LineAxis(Graph, LineNode)
        RequireFields(RuleNode, {"constraintType": CodeValue})
        CheckRuleFrame(Graph, Context, RuleNode, (LineNode,))
        ByLine[LineNode.Identity] = SketchRelation(
            RuleNode.Identity, KindValue, (ConstraintRef(LineNode.Identity),)
        )
    if len(ByLine) != 4:
        raise ValueError(
            "Native rectangle axis rules do not cover the selected perimeter"
        )
    return tuple(ByLine.values())


# the line direction determines which native axis rule can constrain the saved side
def LineAxis(Graph: NativeGraph, LineNode: NativeNode) -> tuple[ConstraintKind, int]:
    Start = ResolveField(Graph, LineNode, "rStartPoint", "Point3D")
    Finish = ResolveField(Graph, LineNode, "rEndPoint", "Point3D")
    First = PointCoords(Start.Fields["point"])
    Final = PointCoords(Finish.Fields["point"])
    if First[1] == Final[1] and First[0] != Final[0]:
        return ConstraintKind.KHorizontal, 64
    if First[0] == Final[0] and First[1] != Final[1]:
        return ConstraintKind.KVertical, 128
    raise ValueError("Native rectangle axis rule refers to a nonaxis side")


# original constraint subjects bind the same objects as their semantic operands
def CheckRuleFrame(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    RuleNode: NativeNode,
    Subjects: tuple[NativeNode, ...],
) -> None:
    RequireFields(
        RuleNode, {"ParentNode": LocalRef(Context.Sketch.ObjectId), "isVisible": False}
    )
    Metadata = tuple(
        (Subject.FieldName, Subject.TypeName, Subject.Value)
        for Subject in RuleNode.Frame.Metadata or ()
    )
    Actual = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in RuleNode.Frame.Subjects or ()
    )
    if Metadata != (
        ("EntityGenesis", "IntrinsicMetaTypeuint64", 2),
    ) or Actual != tuple((NodeValue, 0) for NodeValue in Subjects):
        raise ValueError(
            "Native rectangle rule operands disagree with the authored observer links"
        )
