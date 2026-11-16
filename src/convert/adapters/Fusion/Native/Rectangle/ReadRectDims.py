# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

# the supported source table binds the length drivers along with blind depth and explicit zero taper
KRectParams = ("width_mm", "height_mm", "depth_mm", "d4")


# exact allocation and paired observer ranks keep the four native drivers in their original roles
def ReadRectDims(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimensions: tuple[NativeNode, ...],
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
) -> tuple[tuple[NativeNode, ...], tuple[NativeNode, ...], tuple[SketchRelation, ...]]:
    SketchBindings = LinkedNodes(Graph, Context.SketchFeature, "dcParameters")
    if len(SketchBindings) != 2:
        raise ValueError("Native constrained rectangle requires two sketch bindings")
    Bindings = (*SketchBindings, Context.Along, Context.Taper)
    SameNodes(Bindings, Graph.ByClass("DcDoubleParameter"))
    Owners = (Context.SketchFeature,) * 2 + (Context.Extrude,) * 2
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    DcNodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    Children = LinkedNodes(Graph, DcNodes, "children")
    if any(Children.count(Binding) != 1 for Binding in Bindings):
        raise ValueError(
            "Native constrained rectangle bindings are absent from the fragment"
        )
    Params = tuple(
        CheckRectBind(Graph, Binding, Owner, Table, DcNodes, SlotValue)
        for SlotValue, (Binding, Owner) in enumerate(
            zip(Bindings, Owners, strict=True), start=1
        )
    )
    CheckRectIndex(Graph, Context, Table, Params)
    CheckRectDeps(Graph, Context, SketchBindings)
    Kinds = (ConstraintKind.KDistanceX, ConstraintKind.KDistanceY)
    Relations = tuple(
        ReadRectDim(Graph, Context, Dimension, Binding, Param, Lines, Anchor, KindValue)
        for Dimension, Binding, Param, KindValue in zip(
            Dimensions, SketchBindings, Params[:2], Kinds, strict=True
        )
    )
    Ranks = tuple(
        Dimension.Frame.Subjects[0].ObserverIndex
        for Dimension in Dimensions
        if Dimension.Frame.Subjects
    )
    if Ranks not in ((2, 3), (4, 5)):
        raise ValueError("Native rectangle dimension settings observer ranks disagree")
    return SketchBindings, Params[:2], Relations


# every saved binding and its update must return to the expected feature and parameter table
def CheckRectBind(
    Graph: NativeGraph,
    Binding: NativeNode,
    Owner: NativeNode,
    Table: NativeNode,
    DcNodes: NativeNode,
    SlotValue: int,
) -> NativeNode:
    Param = ResolveField(Graph, Binding, "parameter", "Parameter")
    Update = ResolveField(Graph, Binding, "rDynamicUpdateData", "DynamicUpdateData")
    RequireFields(
        Binding,
        {
            "rrOwnerFeature": LocalRef(Owner.ObjectId),
            "rParentFeature": LocalRef(Owner.ObjectId),
            "rParent": LocalRef(DcNodes.ObjectId),
            "rparamId": SlotValue,
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "rGroupRepresentative": None,
        },
    )
    RequireFields(
        Param,
        {
            "rParent": LocalRef(Table.ObjectId),
            "dcParameter": LocalRef(Binding.ObjectId),
            "creationIndex": SlotValue,
            "userName": KRectParams[SlotValue - 1],
            "unit": "deg" if SlotValue == 4 else "mm",
            "isUserDefined": False,
            "isDriven": False,
            "group": None,
            "rClientObject": None,
        },
    )
    RequireFields(
        Update,
        {
            "rOwnerNode": LocalRef(Binding.ObjectId),
            "isBodyOK": False,
            "isPredecessorOK": False,
            "xRefPredecessorsHash": 0,
        },
    )
    EmptyFields(Update, ("bodies", "predecessors"))
    Amount = NumberValue(Param.Fields["value"])
    if Amount != NumberValue(Binding.Fields["value"]) or (
        Amount != 0.0 if SlotValue == 4 else Amount <= 0.0
    ):
        raise ValueError("Native rectangle saved driver values or zero taper disagree")
    return Param


# the named table and its observer roster cannot include a second driver or hidden global alias
def CheckRectIndex(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Table: NativeNode,
    Params: tuple[NativeNode, ...],
) -> None:
    SameNodes(Params, Graph.ByClass("Parameter"))
    if LinkedNodes(Graph, Table, "children") != Params:
        raise ValueError("Native rectangle model parameter order differs")
    RequireFields(Table, {"highWaterMark": 4})
    RequireFields(Context.Fragment, {"nextParamId": 4})
    Index = ResolveField(
        Graph, Table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    Entries = MappingItems(Index.Fields["parameterMap"])
    if len(Entries) != 4 or {
        Entry.First: Graph.Resolve(Entry.Second) for Entry in Entries
    } != dict(zip(KRectParams, Params, strict=True)):
        raise ValueError("Native rectangle named parameter inventory disagrees")
    Subjects = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in Index.Frame.Subjects or ()
    )
    if Subjects != tuple((NodeValue, 0) for NodeValue in (Table, *Params)):
        raise ValueError("Native rectangle parameter name index observers disagree")


# native dimension operands must measure the proper anchored side in their original direction
def ReadRectDim(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimension: NativeNode,
    Binding: NativeNode,
    Param: NativeNode,
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
    KindValue: ConstraintKind,
) -> SketchRelation:
    IsWidth = KindValue is ConstraintKind.KDistanceX
    RequireFields(
        Dimension,
        {
            "constraintType": 1 << (22 if IsWidth else 23),
            "ParentNode": LocalRef(Context.Sketch.ObjectId),
            "rParent": LocalRef(Context.Sketch.ObjectId),
            "dcParameter": LocalRef(Binding.ObjectId),
            "isSick": False,
            "isVisible": False,
            "rClientObject": None,
        },
    )
    Nodes = LinkedNodes(Graph, Dimension, "geometries")
    Matches = tuple(
        LineNode
        for LineNode in Lines
        if (
            Graph.Resolve(LineNode.Fields["rStartPoint"]),
            Graph.Resolve(LineNode.Fields["rEndPoint"]),
        )
        == Nodes
    )
    if len(Nodes) != 2 or len(Matches) != 1 or Nodes[int(not IsWidth)] != Anchor:
        raise ValueError(
            "Native rectangle dimension does not measure its exact ordered anchored side"
        )
    Points = tuple(PointCoords(NodeValue.Fields["point"]) for NodeValue in Nodes)
    CheckDimCache(Dimension.Fields, Param, Points, IsWidth)
    CheckDimFrame(Graph, Dimension, Nodes, Anchor, IsWidth)
    return SketchRelation(
        Dimension.Identity,
        KindValue,
        tuple(ConstraintRef(NodeValue.Identity) for NodeValue in Nodes),
        parameter_id=Param.Identity,
    )


# stale presentation extension points stay in source state while the measured carrier is checked
def CheckDimCache(
    Fields: dict[str, KEntityValue],
    Param: NativeNode,
    Points: tuple[tuple[float, float, float], ...],
    IsWidth: bool,
) -> None:
    InfoValue = ObjectFields(Fields["LinearDimensionInfo"])
    Start, Finish = Points
    AxisValue = int(not IsWidth)
    Amount = NumberValue(Param.Fields["value"])
    Other = Finish if IsWidth else Start
    SameNumbers(Other, (Amount, 0.0, 0.0) if IsWidth else (0.0, Amount, 0.0))
    SameNumbers(
        (Distance(Start, Finish), NumberValue(InfoValue["length"])), (Amount, Amount)
    )
    SameNumbers(PointCoords(InfoValue["startPoint"]), Start)
    SameNumbers(PointCoords(InfoValue["endPoint"]), Finish)
    Plane = ObjectFields(InfoValue["plane"])
    Extension = PointCoords(InfoValue["extnStartPoint"])
    if (
        InfoValue["bDriven"] is not False
        or InfoValue["hasTextPoint"] is not True
        or InfoValue["isSingleArrow"] is not False
        or InfoValue["prefix"] != ""
        or InfoValue["text"] != Param.Fields["expression"]
        or Plane["normalReversed"] is not False
        or PointCoords(Plane["origin"]) != (0.0, 0.0, 0.0)
        or PointCoords(Plane["uAxis"]) != (1.0, 0.0, 0.0)
        or PointCoords(Plane["vAxis"]) != (0.0, 1.0, 0.0)
        or SeriesItems(Fields["RefPositions"]) != (0.0, 1.0)
        or Extension[1 - AxisValue] != 0.0
        or Extension[2] != 0.0
        or not 0.0 <= Extension[AxisValue] <= Amount
    ):
        raise ValueError(
            "Native rectangle dimension has inconsistent literal or annotation placement"
        )
    CheckDimLayout(InfoValue, Start, Finish, AxisValue)


# the dimension carrier stays on the source axis with a consistent text and extension offset
def CheckDimLayout(
    InfoValue: dict[str, KEntityValue],
    Start: tuple[float, float, float],
    Finish: tuple[float, float, float],
    AxisValue: int,
) -> None:
    First = PointCoords(InfoValue["DimStartPoint"])
    Second = PointCoords(InfoValue["DimEndPoint"])
    Caption = PointCoords(InfoValue["textPosition"])
    SideAxis = 1 - AxisValue
    SameNumbers(
        (First[AxisValue], Second[AxisValue], Caption[AxisValue]),
        (
            Start[AxisValue],
            Finish[AxisValue],
            (Start[AxisValue] + Finish[AxisValue]) / 2,
        ),
    )
    SameNumbers(
        (First[2], Second[2], Caption[2], Second[SideAxis], Caption[SideAxis]),
        (0.0, 0.0, 0.0, First[SideAxis], First[SideAxis]),
    )


# dimension observers bind the shared anchor and independent perimeter point by their original ranks
def CheckDimFrame(
    Graph: NativeGraph,
    Dimension: NativeNode,
    Nodes: tuple[NativeNode, ...],
    Anchor: NativeNode,
    IsWidth: bool,
) -> None:
    Settings = Graph.OneClass("CommonDataAssetSettings")
    Other = Nodes[int(IsWidth)]
    Subjects = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in Dimension.Frame.Subjects or ()
    )
    Metadata = tuple(
        (Subject.FieldName, Subject.TypeName, Subject.Value)
        for Subject in Dimension.Frame.Metadata or ()
    )
    if (
        len(Subjects) != 3
        or Subjects[0][0] != Settings
        or Subjects[1:] != ((Anchor, 1 if IsWidth else 2), (Other, 0))
        or Metadata != (("EntityGenesis", "IntrinsicMetaTypeuint64", 0),)
    ):
        raise ValueError(
            "Native rectangle dimension observers do not follow the anchored operands"
        )


# the complete connected first boss dependency graph must follow the verified scoped sketch drivers
def CheckRectDeps(
    Graph: NativeGraph, Context: ExtrudeContext, SketchBindings: tuple[NativeNode, ...]
) -> None:
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (PlaneRef,) = LinkedNodes(Graph, Matrix, "dataRefs")
    (Profile,) = LinkedNodes(Graph, Context.Extrude, "profileDataRefs")
    (Region,) = LinkedNodes(Graph, Profile, "dataRefs")
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Component = Graph.OneClass("DcComponent").ObjectId
    Sketch, BossId = Context.SketchFeature.ObjectId, Context.Extrude.ObjectId
    Plane, Place = PlaneRef.ObjectId, Matrix.ObjectId
    Width, Height = (NodeValue.ObjectId for NodeValue in SketchBindings)
    RegionId, ProfileId, ToolId = Region.ObjectId, Profile.ObjectId, ToolNode.ObjectId
    Along, Taper = Context.Along.ObjectId, Context.Taper.ObjectId
    Order = (
        Component,
        Plane,
        Place,
        Width,
        Height,
        Sketch,
        RegionId,
        ProfileId,
        Along,
        Taper,
        ToolId,
        BossId,
    )
    Edges = {
        (Component, Sketch, 4096),
        (Component, BossId, 4096),
        (Plane, Place, 1),
        (Place, Sketch, 1),
        (Width, Sketch, 1),
        (Height, Sketch, 1),
        (Sketch, RegionId, 4),
        (RegionId, ProfileId, 1),
        (ProfileId, ToolId, 1),
        (Along, ToolId, 1),
        (Taper, ToolId, 1),
        (ToolId, BossId, 1),
    }
    Compute = ResolveField(
        Graph, Context.Fragment, "rComputeManager", "DcComputeManager"
    )
    Dependencies = ResolveField(
        Graph, Context.Fragment, "rDependencyManager", "DcDependencyManager"
    )
    RequireFields(Compute, {"sortIsCurrent": True})
    RequireFields(Dependencies, {"mapsAreCurrent": True})
    if (
        tuple(
            NodeValue.ObjectId
            for NodeValue in LinkedNodes(Graph, Compute, "sortedNodesAll")
        )
        != Order
        or ReadRectEdges(Graph, Dependencies.Fields["successorMap"]) != Edges
        or ReadRectEdges(Graph, Dependencies.Fields["predecessorMap"])
        != {(Second, First, KindValue) for First, Second, KindValue in Edges}
    ):
        raise ValueError(
            "Native rectangle compute order or reciprocal dependencies disagree"
        )
    SameNodes(
        LinkedNodes(Graph, Context.SketchFeature, "childNodes"),
        (PlaneRef, Matrix, *SketchBindings),
    )


# dependency tuples retain the typed link kind and reject duplicate saved incidences
def ReadRectEdges(Graph: NativeGraph, Value: KEntityValue) -> set[tuple[int, int, int]]:
    Edges = [
        (
            Graph.Resolve(Entry.First).ObjectId,
            Graph.Resolve(Other.First).ObjectId,
            IntegerValue(Other.Second),
        )
        for Entry in MappingItems(Value)
        for Other in MappingItems(Entry.Second)
    ]
    Result = set(Edges)
    if len(Result) != len(Edges):
        raise ValueError("Native rectangle contains duplicated dependency edges")
    return Result
