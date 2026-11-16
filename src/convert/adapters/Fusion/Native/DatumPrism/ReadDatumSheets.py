# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.DatumPrism.ReadDatumFrame import LocalDatum
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import (
    CheckRegionTags,
    KCurveMap,
)
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import CheckSectionOwn
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
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegionEdge import (
    CheckRegionEdge,
)
from interchange.geometry.Models.Transform import Transform


# the two differently placed sheet roots must own distinct geometry and reciprocal selected curve links
def ReadDatumSheets(
    Snapshot: GeometryState,
    FrameValue: Transform,
    Curves: KCurveMap,
    Occupied: set[int],
) -> frozenset[int]:
    WireValue = ReadSnapWire(EmitGeometry(Snapshot), RecordCount=170)
    First = MapRegion(WireValue.Table, 2, 88, 152)
    Second = MapRegion(WireValue.Table, 3, 113, 160)
    FirstSlots, SecondSlots = set(First.values()), set(Second.values())
    SectionSlots = frozenset(FirstSlots | SecondSlots)
    if FirstSlots & SecondSlots or SectionSlots & (Occupied | {0, 1, 2, 3, 5, 7}):
        raise ValueError("Native YZ auxiliary sections share geometry owners")
    Profile = ReadRegion(WireValue.Table, First, 88, 152)
    Sketch = ReadRegion(WireValue.Table, Second, 113, 160)
    CheckDatumSheet(Profile, FrameValue, Curves, World=True)
    CheckDatumSheet(Sketch, FrameValue, Curves)
    CheckSectionOwn(Snapshot, First, 88, 152)
    CheckSectionOwn(Snapshot, Second, 113, 160)
    return SectionSlots


# retain the original section plane and compare its selected edges in the local sketch frame
def CheckDatumSheet(
    Region: RegionFrame,
    FrameValue: Transform,
    Curves: KCurveMap,
    World: bool = False,
) -> None:
    Normal = (1.0, 0.0, 0.0) if World else (0.0, 0.0, 1.0)
    Basis = (0.0, 0.0, -1.0) if World else (1.0, 0.0, 0.0)
    Corners = Region.CornersCm
    if (
        Region.Plane.ReverseV
        or Region.Plane.Normal != Normal
        or Region.Plane.Basis != Basis
    ):
        raise ValueError("Native YZ section has an incorrect saved plane frame")
    SameNumbers(
        Region.Plane.OriginCm,
        tuple(sum(Point[AxisValue] for Point in Corners) / 4 for AxisValue in range(3)),
    )
    for Index, EdgeValue in enumerate(Region.Edges):
        if Region.VertexOwners[Index] not in (Index, (Index - 1) % 4):
            raise ValueError("Native YZ section vertex owner is not incident")
        CheckRegionEdge(EdgeValue, Corners[Index], Corners[(Index + 1) % 4])
    Local = (
        tuple(LocalDatum(FrameValue, Point) for Point in Corners) if World else Corners
    )
    if any(Point[2] != 0.0 for Point in Local):
        raise ValueError("Native YZ section leaves the selected sketch plane")
    CheckRegionTags(ReplaceValue(Region, CornersCm=Local), Curves)
