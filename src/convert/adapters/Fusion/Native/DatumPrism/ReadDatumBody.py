# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.DatumPrism.ReadDatumFrame import LocalDatum
from convert.adapters.Fusion.Native.DatumPrism.ReadDatumSheets import ReadDatumSheets
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedOwners import CheckOwnTags
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import (
    CheckEdgeTags,
    CheckFaceTags,
    ReadFeatureTags,
    SelectedCurves,
)
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import (
    CheckCuboid,
    CheckSignedMass,
    ReadInsert,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.geometry.Models.Transform import Transform

# the measured solid and world profile carry an explicit identity placement node
KDatumIdentity = TransformNode(
    -1,
    -1,
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0),
    1.0,
    False,
    False,
    False,
)


# both closed solids must match the same selected sketch frame and saved feature operation
def ReadDatumBody(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    History: JournalModel,
    Snapshot: GeometryState,
    FrameValue: Transform,
) -> None:
    HistoryTable, Journal = ReadInsert(History)
    SavedTable, Saved = ReadDatumSolid(Snapshot, Journal.StateId)
    JournalView = LocalBox(Journal, FrameValue)
    SavedView = LocalBox(Saved, FrameValue)
    Extent = NumberValue(Context.Along.Fields["value"])
    Lower = (Shape.BasePoint[0] / 10, Shape.BasePoint[1] / 10, 0.0)
    Upper = (Lower[0] + Shape.Width / 10, Lower[1] + Shape.Depth / 10, Extent)
    _ = CheckCuboid(HistoryTable, JournalView, Lower, Upper)
    Occupied = CheckCuboid(SavedTable, SavedView, Lower, Upper)
    Curves = SelectedCurves(Shape)
    JournalTags = ReadFeatureTags(HistoryTable)
    BodyTag = JournalTags.pop(Journal.BodyRef, None)
    if BodyTag is None:
        raise ValueError("Native YZ prism has no owned body tag")
    Operation, Sides = CheckOwnTags(
        Graph, Context, Model, Shape, History, Journal, BodyTag
    )
    if set(Sides.values()) != set(Curves):
        raise ValueError("Native YZ side tags omit selected curves")
    HistoryFaces = CheckFaceTags(
        JournalView, JournalTags, Operation, Extent, Sides, Curves
    )
    SavedFaces = CheckFaceTags(
        SavedView, ReadFeatureTags(SavedTable), Operation, Extent, Sides, Curves
    )
    if HistoryFaces != SavedFaces:
        raise ValueError("Native YZ history and snapshot name different physical faces")
    SectionSlots = ReadDatumSheets(Snapshot, FrameValue, Curves, Occupied)
    CheckEdgeTags(HistoryTable, Curves, Extent, 2, FrameValue)
    CheckEdgeTags(SavedTable, Curves, Extent, 2, FrameValue, SectionSlots)
    LowerWorld, UpperWorld = WorldBounds(Journal)
    CheckSignedMass(Context, LowerWorld, UpperWorld)


# the typed snapshot distinguishes the solid and the two section root placements
def ReadDatumSolid(
    Snapshot: GeometryState, Current: int
) -> tuple[LiveTable, PlanarShell]:
    Roots = tuple(
        (SlotValue, Value.TransformRef)
        for SlotValue, Value in enumerate(Snapshot.Entities)
        if isinstance(Value, BodyNode)
    )
    if (
        Snapshot.Header.RootCount != 4
        or len(Snapshot.Entities) != 170
        or Roots != ((1, 5), (2, 7), (3, -1))
        or Snapshot.Entities[5] != KDatumIdentity
        or Snapshot.Entities[7] != KDatumIdentity
    ):
        raise ValueError("Native YZ snapshot has unsupported root placements")
    Slots = tuple(range(len(Snapshot.Entities)))
    Table = LiveTable(Current, Snapshot.Entities, Slots, Slots, Slots)
    return Table, ReadPlacedBody(Table, 1)


# only a comparison view omits the independently verified identity placement
def LocalBox(Solid: PlanarShell, FrameValue: Transform) -> PlanarShell:
    if Solid.Placement != KDatumIdentity:
        raise ValueError("Native YZ solid must carry its saved identity placement")
    return ReplaceValue(
        Solid,
        PointsCm=tuple(LocalDatum(FrameValue, Point) for Point in Solid.PointsCm),
        Placement=None,
    )


# mass and inertia remain expressed in the actual saved world coordinates
def WorldBounds(Solid: PlanarShell) -> tuple[KJournalVector, KJournalVector]:
    AxisX, AxisY, AxisZ = zip(*Solid.PointsCm, strict=True)
    return (min(AxisX), min(AxisY), min(AxisZ)), (max(AxisX), max(AxisY), max(AxisZ))
