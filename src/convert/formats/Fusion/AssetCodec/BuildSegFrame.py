# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.AssetCodec.SegmentPlan import SegmentPlan
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import KMaxAuxBytes


# native asset paths and manifest ordinals must agree with emitted segment headers
def BuildSegFrame(
    Value: SegmentPlan, Segment: SegmentKind, SegmentId: int
) -> SegmentFrame:
    if (
        not isinstance(CastValue(object, Value), SegmentPlan)
        or not isinstance(CastValue(object, Value.Metadata), MetaSegment)
        or not isinstance(CastValue(object, Value.Metadata.Header), MetaHeader)
        or Value.Metadata.Header.Segment is not Segment
        or Value.Metadata.Header.SegmentId != SegmentId
        or type(Value.Records) is not tuple
    ):
        raise ValueError("Fusion asset segment plan does not match its manifest slot")
    BulkData, MetaData = EmitSegment(Value.Metadata, Value.Records)
    if (
        Segment is not SegmentKind.KDesign
        and max(len(BulkData), len(MetaData)) > KMaxAuxBytes
    ):
        raise ValueError("Fusion asset auxiliary segment exceeds reader limit")
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=Segment)
    Owners = {Entry.ObjectId: Entry for Entry in Spans if Entry.IsPrimary}
    return SegmentFrame(Segment, BulkData, MetaData, Spans, Owners)
