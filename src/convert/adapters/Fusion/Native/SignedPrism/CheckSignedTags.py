# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter as CountLabels

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedOwners import CheckOwnTags
from convert.adapters.Fusion.Native.SignedPrism.SignedBody import SignedBody
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

# selected design lines determine the expected physical endpoints for each native tag
KCurveMap = dict[int, frozenset[tuple[float, float]]]


# both closed solid forms and separate sections must identify the same selected sketch and operation
def CheckSignedTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    History: JournalModel,
    BodyValue: SignedBody,
) -> None:
    JournalTags = ReadFeatureTags(BodyValue.JournalTable)
    BodyTag = JournalTags.pop(BodyValue.Journal.BodyRef, None)
    if BodyTag is None:
        raise ValueError("Native reverse prism has no owned body tag")
    Operation, Sides = CheckOwnTags(
        Graph, Context, Model, Shape, History, BodyValue.Journal, BodyTag
    )
    Curves = SelectedCurves(Shape)
    if set(Sides.values()) != set(Curves):
        raise ValueError("Native reverse prism side tags omit selected curves")
    Extent = NumberValue(Context.Along.Fields["value"])
    JournalFaces = CheckFaceTags(
        BodyValue.Journal, JournalTags, Operation, Extent, Sides, Curves
    )
    SavedFaces = CheckFaceTags(
        BodyValue.Saved,
        ReadFeatureTags(BodyValue.SavedTable),
        Operation,
        Extent,
        Sides,
        Curves,
    )
    if JournalFaces != SavedFaces:
        raise ValueError(
            "Native reverse prism history and snapshot disagree about face tags"
        )
    for Region in BodyValue.Regions:
        CheckRegionTags(Region, Curves)
    CheckEdgeTags(BodyValue.JournalTable, Curves, Extent, 2)
    CheckEdgeTags(BodyValue.SavedTable, Curves, Extent, 6)


# live owned tags have exactly one group and one resolved topology recipient
def ReadFeatureTags(Table: LiveTable) -> dict[int, FeatureTag]:
    TagMap: dict[int, FeatureTag] = {}
    for SlotValue in Table.LiveSlots:
        Value = Table.Entities[SlotValue]
        if not isinstance(Value, TagAttrib):
            continue
        Owner = StableRef(Table, Value.Links.OwnerRef)
        if Owner in TagMap or len(Value.Groups) != 1:
            raise ValueError("Ambiguous native reverse prism feature tag owner")
        TagMap[Owner] = Value.Groups[0]
    return TagMap


# distinct original curve tags must identify each side of the closed native selection
def SelectedCurves(Shape: RectGeometry) -> KCurveMap:
    Curves = {
        CurveTag(NodeValue): frozenset(
            (
                (LineValue.start.x / 10, LineValue.start.y / 10),
                (LineValue.end.x / 10, LineValue.end.y / 10),
            )
        )
        for NodeValue, LineValue in zip(Shape.LineNodes, Shape.Lines, strict=True)
    }
    if len(Curves) != 4:
        raise ValueError("Native reverse prism requires four tagged Design curves")
    return Curves


# each face tag must own the measured cap station or its selected physical side
def CheckFaceTags(
    Shell: PlanarShell,
    TagMap: dict[int, FeatureTag],
    Operation: int,
    Extent: float,
    Sides: dict[str, int],
    Curves: KCurveMap,
) -> dict[str, frozenset[KJournalVector]]:
    Faces: dict[str, frozenset[KJournalVector]] = {}
    if set(Shell.FaceRefs) != set(TagMap):
        raise ValueError("Native reverse prism must tag every closed solid face")
    for SlotValue, RingValue in zip(Shell.FaceRefs, Shell.Rings, strict=True):
        Points = frozenset(Shell.PointsCm[Index] for Index in RingValue)
        TagValue = TagMap[SlotValue]
        FaceName = TagValue.PrimaryId
        Stations = {Point[2] for Point in Points}
        if FaceName in Faces or TagValue != FeatureTag(FaceName, (Operation,), 0, 0):
            raise ValueError("Native reverse prism face tag owns the wrong operation")
        if FaceName in ("1", "2"):
            if Stations != {0.0 if FaceName == "1" else Extent}:
                raise ValueError(
                    "Native reverse prism cap tag owns the wrong signed station"
                )
        elif (
            FaceName not in Sides
            or Stations != {0.0, Extent}
            or frozenset(
                (XValue, YValue) for XValue, YValue, ZValue in Points if ZValue == 0.0
            )
            != Curves[Sides[FaceName]]
        ):
            raise ValueError(
                "Native reverse prism face tag owns a different selected curve"
            )
        Faces[FaceName] = Points
    if set(Faces) != {"1", "2", *Sides}:
        raise ValueError("Native reverse prism face tag coverage is incomplete")
    return Faces


# source links must point to the actual live edge or coedge of their physical curve
def CheckEdgeTags(
    Table: LiveTable, Curves: KCurveMap, Extent: float, Count: int
) -> None:
    Labels: CountLabels[int] = CountLabels()
    for SlotValue in Table.LiveSlots:
        Value = Table.Entities[SlotValue]
        if not isinstance(Value, SketchAttrib):
            continue
        Owner = StableRef(Table, Value.Links.OwnerRef)
        Coedge = Table.Entities[Owner]
        EdgeSlot = Owner
        Direction = 1
        if isinstance(Coedge, CoedgeNode):
            EdgeSlot = StableRef(Table, Coedge.EdgeRef)
            Direction = 0
        EdgeValue = RequireLive(Table, EdgeSlot, EdgeNode)
        Start, Finish = (
            ReadVertexPoint(Table, StableRef(Table, Index))
            for Index in (EdgeValue.StartVertex, EdgeValue.EndVertex)
        )
        LinkValue = Value.SourceLink
        if (
            LinkValue.PrimaryId not in Curves
            or LinkValue != SketchLink(LinkValue.PrimaryId, 0, Direction, 1, 1)
            or Start[2] != Finish[2]
            or Start[2] not in (0.0, Extent)
            or frozenset((Start[:2], Finish[:2])) != Curves[LinkValue.PrimaryId]
        ):
            raise ValueError(
                "Native reverse prism sketch tag owns a different physical edge"
            )
        Labels[LinkValue.PrimaryId] += 1
    if dict(Labels) != dict.fromkeys(Curves, Count):
        raise ValueError(
            "Native reverse prism sketch source-link coverage is incomplete"
        )


# a distinct section must reproduce all four selected physical curves and their tag directions
def CheckRegionTags(Region: RegionFrame, Curves: KCurveMap) -> None:
    Corners = Region.CornersCm
    LastPoints = (*Corners[1:], Corners[0])
    if {TagValue.PrimaryId for TagValue in Region.CoedgeTags} != set(Curves):
        raise ValueError("Native reverse prism section lacks a selected curve")
    for Start, Finish, Coedge, EdgeValue in zip(
        Corners, LastPoints, Region.CoedgeTags, Region.EdgeTags, strict=True
    ):
        TagValue = Coedge.PrimaryId
        if (
            Coedge != SketchLink(TagValue, 0, 0, 1, 1)
            or EdgeValue != SketchLink(TagValue, 0, 1, 1, 1)
            or frozenset((Start[:2], Finish[:2])) != Curves[TagValue]
        ):
            raise ValueError(
                "Native reverse prism section curve tag disagrees with the selected loop"
            )
