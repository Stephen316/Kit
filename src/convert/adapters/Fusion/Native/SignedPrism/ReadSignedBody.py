# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from itertools import product as GridPoints
from math import prod as Product

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Policy.CheckMassCache import CheckBoxInertia
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.SignedBody import SignedBody
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadRegion import (
    ReadRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadSnapWire import (
    ReadSnapWire,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegion import (
    CheckRegion,
)
from convert.Formats.Fusion.DocumentCodec.Reading.IsInsertHistory import IsInsertHistory


# a reverse body must resolve independently in both native geometry roles
def ReadSignedBody(
    Context: ExtrudeContext,
    Shape: RectGeometry,
    History: JournalModel,
    Snapshot: GeometryState,
) -> SignedBody:
    Depth = NumberValue(Context.Along.Fields["value"])
    if not Depth < 0.0 or Shape.BasePoint != (0.0, 0.0, 0.0):
        raise ValueError(
            "Native reverse prism requires negative depth at the XY origin"
        )
    Lower = (0.0, 0.0, Depth)
    Upper = (Shape.Width / 10, Shape.Depth / 10, 0.0)
    HistoryTable, Journal = ReadInsert(History)
    SavedTable, Saved = ReadSavedSolid(Snapshot, Journal.StateId)
    _ = CheckCuboid(HistoryTable, Journal, Lower, Upper)
    Occupied = CheckCuboid(SavedTable, Saved, Lower, Upper)
    Regions = ReadSections(Snapshot, Saved, Occupied)
    CheckSignedMass(Context, Lower, Upper)
    return SignedBody(Journal, Saved, HistoryTable, SavedTable, Regions)


# the operation starts at an empty state and inserts one fully owned live solid
def ReadInsert(History: JournalModel) -> tuple[LiveTable, PlanarShell]:
    if not IsInsertHistory(History):
        raise ValueError("Native reverse prism requires one complete insertion")
    Active, Before = Materialize(History)
    if (
        Active.StateId != History.Stream.CurrentStateId
        or Active.StateId != History.Stream.MaxStateId
        or Before.StateId >= Active.StateId
        or Before.Versions != ((0, 0),)
        or len(Active.Versions) != History.ActiveCount
    ):
        raise ValueError("Native reverse prism insertion states disagree")
    Bodies = ReadPlanarState(History, Active.StateId)
    Table = MakeLiveTable(History, Active.StateId)
    if (
        len(Bodies) != 1
        or ReadPlanarState(History, Before.StateId)
        or tuple(
            SlotValue
            for SlotValue in Table.LiveSlots
            if isinstance(Table.Entities[SlotValue], BodyNode)
        )
        != (Bodies[0].BodyRef,)
    ):
        raise ValueError("Native reverse prism insertion must own one live solid")
    return Table, Bodies[0]


# a typed snapshot has one independent untransformed solid and two sheet roots
def ReadSavedSolid(
    Snapshot: GeometryState,
    Current: int,
) -> tuple[LiveTable, PlanarShell]:
    Roots = tuple(
        (SlotValue, Value.TransformRef)
        for SlotValue, Value in enumerate(Snapshot.Entities)
        if isinstance(Value, BodyNode)
    )
    if Snapshot.Header.RootCount != 4 or Roots != ((1, -1), (2, -1), (3, -1)):
        raise ValueError(
            "Native reverse prism snapshot requires three untransformed roots"
        )
    Slots = tuple(range(len(Snapshot.Entities)))
    Table = LiveTable(Current, Snapshot.Entities, Slots, Slots, Slots)
    return Table, ReadPlacedBody(Table, 1)


# the selected rectangle and signed depth must explain every saved cuboid coordinate
def CheckCuboid(
    Table: LiveTable,
    Shell: PlanarShell,
    Lower: KJournalVector,
    Upper: KJournalVector,
) -> set[int]:
    Faces = ReadBodyFaces(Table, Shell.BodyRef)
    Edges = {
        UseValue.EdgeRef for FaceValue in Faces for UseValue in FaceValue.BoundaryUses
    }
    if (
        Shell.Placement is not None
        or len(Shell.VertexRefs) != 8
        or len(Shell.FaceRefs) != 6
        or len(Edges) != 12
        or any(len(RingValue) != 4 for RingValue in Shell.Rings)
        or set(Shell.PointsCm) != set(GridPoints(*zip(Lower, Upper, strict=True)))
    ):
        raise ValueError(
            "Native reverse prism signed geometry disagrees with the selected rectangle"
        )
    SameNumbers(
        (Shell.VolumeCm3,),
        (
            Product(
                UpperValue - LowerValue
                for LowerValue, UpperValue in zip(Lower, Upper, strict=True)
            ),
        ),
    )
    return SolidSlots(Table, Shell, Edges)


# disjoint sections cannot borrow any geometric record owned by the saved solid
def SolidSlots(Table: LiveTable, Shell: PlanarShell, Edges: set[int]) -> set[int]:
    BodyValue = RequireLive(Table, Shell.BodyRef, BodyNode)
    LumpValue = RequireLive(Table, BodyValue.FirstLump, LumpNode)
    Faces = tuple(
        RequireLive(Table, SlotValue, FaceNode) for SlotValue in Shell.FaceRefs
    )
    return {
        Shell.BodyRef,
        BodyValue.FirstLump,
        LumpValue.FirstShell,
        *Shell.FaceRefs,
        *Shell.VertexRefs,
        *Edges,
        *(FaceValue.FirstLoop for FaceValue in Faces),
        *(FaceValue.Surface for FaceValue in Faces),
        *(
            UseValue.CoedgeRef
            for FaceValue in ReadBodyFaces(Table, Shell.BodyRef)
            for UseValue in FaceValue.BoundaryUses
        ),
        *(RequireLive(Table, SlotValue, EdgeNode).CurveRef for SlotValue in Edges),
        *(
            RequireLive(Table, SlotValue, VertexNode).PointRef
            for SlotValue in Shell.VertexRefs
        ),
    }


# each auxiliary ring owns a complete planar section of the same selected profile
def ReadSections(
    Snapshot: GeometryState,
    Solid: PlanarShell,
    Occupied: set[int],
) -> tuple[RegionFrame, RegionFrame]:
    WireValue = ReadSnapWire(EmitGeometry(Snapshot))
    Corners = tuple(Point for Point in Solid.PointsCm if Point[2] == 0.0)
    First = MapRegion(WireValue.Table, 2, 88, 152)
    Second = MapRegion(WireValue.Table, 3, 113, 160)
    if (Occupied | {0, 1, 2, 3}).intersection(
        (*First.values(), *Second.values())
    ) or set(First.values()).intersection(Second.values()):
        raise ValueError("Native reverse prism auxiliary regions share geometry owners")
    Profile = ReadRegion(WireValue.Table, First, 88, 152)
    Sketch = ReadRegion(WireValue.Table, Second, 113, 160)
    CheckSectionOwn(Snapshot, First, 88, 152)
    CheckSectionOwn(Snapshot, Second, 113, 160)
    for Region in (Profile, Sketch):
        CheckRegion(Region, Corners)
        if set(Region.CornersCm) != set(Corners):
            raise ValueError(
                "Native reverse prism auxiliary region leaves the selected plane"
            )
    return Profile, Sketch


# each section attribute must point back to the physical edge or coedge that designated it
def CheckSectionOwn(
    Snapshot: GeometryState,
    Mapping: dict[int, int],
    Start: int,
    Attrib: int,
) -> None:
    for Index in range(8):
        TagValue = Snapshot.Entities[Mapping[Attrib + Index]]
        Owner = Mapping[Start + 5 + Index]
        if not isinstance(TagValue, SketchAttrib) or TagValue.Links.OwnerRef != Owner:
            raise ValueError(
                "Native reverse prism section attribute has a different physical owner"
            )


# a negative station changes the centroid and cross inertia terms without changing the mass scale
def CheckSignedMass(
    Context: ExtrudeContext, Lower: KJournalVector, Upper: KJournalVector
) -> None:
    Width = Upper[0] - Lower[0]
    Height = Upper[1] - Lower[1]
    Depth = Upper[2] - Lower[2]
    Center = tuple(
        (LowerValue + UpperValue) / 2
        for LowerValue, UpperValue in zip(Lower, Upper, strict=True)
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    SameNumbers(
        (
            NumberValue(Cache["volume"]),
            NumberValue(Cache["area"]),
            *PointCoords(Cache["cog"]),
        ),
        (
            Width * Height * Depth,
            2 * (Width * Height + Width * Depth + Height * Depth),
            *Center,
        ),
    )
    CheckBoxInertia(Context, (Width, Height, Depth), Center)
