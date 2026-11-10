# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackData

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPrimitive import KSketchKinds
from interchange.geometry.models.Sketch import Sketch

# the framed native curve tag identifies otherwise unsupported sketch curve records
KCurveTagField = b"\x0e\0\0\0crv_primary_id"


# a missing native cutter must not change the meaning of a selected portion ordinal
def CheckTrimInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchId: int, SketchValue: Sketch
) -> None:
    Projected = {
        int(Entity.provenance.native_id)
        for Entity in SketchValue.entities
        if Entity.provenance is not None
    }
    OwnerRef = PackData("<BQH", 1, SketchId, 0)
    for SpanValue in Owners.values():
        BodyStart = SpanValue.PayloadOffset + 4
        TailStart = SpanValue.EndOffset - 11
        if (
            SpanValue.ObjectId in Projected
            or TailStart < BodyStart
            or BulkData[TailStart : SpanValue.EndOffset] != OwnerRef
        ):
            continue
        if SpanValue.ClassGuid in KSketchKinds or (
            BulkData[BodyStart : BodyStart + 2] == b"\0\1"
            and BulkData.find(KCurveTagField, BodyStart, TailStart) >= 0
        ):
            raise ValueError(
                "Fusion trimmed profile has an unprojected source primitive"
            )
