# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchFrame import ReadFrame
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.SupportPlane import SupportPlane

# only a typed native sketch feature may select a sketch root
KSketchFeature = "8DA771B7-52ED-42FC-94E2-2353FE141373"

# typed sketch continuations own the placement and name fields
KSketchBase = "37AD519C-AFB3-4CE2-9E6D-E3269FC6CDB9"


# forward and reciprocal references prove placement belongs to the timeline sketch
def ResolveSketch(
    BulkData: bytes,
    Feature: RecordSpan,
    Owners: dict[int, RecordSpan],
    Bases: dict[int, list[RecordSpan]],
) -> tuple[RecordSpan, SupportPlane]:
    Cursor = MetaCursor(BulkData[Feature.PayloadOffset + 4 : Feature.EndOffset])
    Cursor.Offset = 3
    Count = Cursor.ReadCount(1024)
    Cursor.Offset = 12 + 11 * Count
    SketchId = ReadNativeRef(Cursor)
    RootSpan = Owners.get(SketchId)
    Candidates = Bases.get(SketchId, [])
    if (
        RootSpan is None
        or RootSpan.ClassGuid != "44A64366-4BD3-4B24-881A-F94C206E8F2D"
        or len(Candidates) != 1
    ):
        raise ValueError("Missing or ambiguous Fusion sketch root")
    RootBody = BulkData[RootSpan.PayloadOffset + 4 : RootSpan.EndOffset]
    if ReadNativeRef(MetaCursor(RootBody[-15:])) != Feature.ObjectId:
        raise ValueError("Fusion sketch root feature reference disagrees")
    (BaseSpan,) = Candidates
    Cursor = MetaCursor(BulkData[BaseSpan.PayloadOffset + 4 : BaseSpan.EndOffset])
    FrameId = ReadNativeRef(Cursor)
    Cursor.Offset = 28
    NameValue = Cursor.ReadText(True, Maximum=1024)
    FrameSpan = Owners.get(FrameId)
    if (
        FrameSpan is None
        or FrameSpan.ClassGuid != "F47A46FB-DA27-4AFA-8A72-1B38FA596E23"
    ):
        raise ValueError("Missing typed Fusion sketch transform")
    Frame, ComponentId = ReadFrame(
        BulkData[FrameSpan.PayloadOffset + 4 : FrameSpan.EndOffset]
    )
    Component = Owners.get(ComponentId)
    if (
        Component is None
        or Component.ClassGuid != "E03784ED-5E19-4E14-B9F2-3B07017018CD"
    ):
        raise ValueError("Missing Fusion sketch transform component")
    Origin = RecordOrigin(FrameSpan)
    PlaneValue = SupportPlane(
        id=f"fusion-sketch-frame-{SketchId}",
        name=NameValue,
        transform=Frame,
        provenance=Replace(Origin, spans=Origin.spans + RecordOrigin(BaseSpan).spans),
        attributes=FreezeMapping(
            {
                "fusion.coordinate_space": "component",
                "fusion.component_object_id": ComponentId,
                "fusion.native_support_resolved": False,
            }
        ),
    )
    return RootSpan, PlaneValue
