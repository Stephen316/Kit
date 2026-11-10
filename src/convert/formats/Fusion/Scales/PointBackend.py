# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from interchange.geometry.models.VectorSpace import SpaceVector

# the owned point backend distinguishes source methods and stores a separate coordinate copy
KPointBackend = "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44"


# native spatial coordinates are converted once before checking their authored sources
def ReadSpatialPt(Cursor: MetaCursor) -> SpaceVector:
    Values = tuple(Value * 10 for Value in Unpack("<3d", Cursor.TakeBytes(24)))
    if not all(IsFinite(Value) for Value in Values):
        raise ValueError("Fusion selected point is nonfinite")
    return SpaceVector(*Values)


# point backend ownership and count qualify the one authored support descriptor
def ReadPointBack(
    BulkData: bytes, Owners: dict[int, RecordSpan], BackendId: int, FeatureId: int
) -> tuple[SpaceVector, int, int]:
    Cursor = SelectCursor(BulkData, Owners, BackendId, KPointBackend)
    if len(Cursor.DataValue) != 178 or Cursor.TakeBytes(23) != bytes(23):
        raise ValueError("Unsupported Fusion point backend framing")
    Cached = ReadSpatialPt(Cursor)
    Method = Cursor.ReadWord()
    Cursor.Offset = 75
    if Cursor.ReadWord() != 1:
        raise ValueError("Fusion point backend must have one support descriptor")
    Descriptor = ReadNativeRef(Cursor)
    Cursor.Offset = 167
    if ReadNativeRef(Cursor) != FeatureId:
        raise ValueError("Fusion point backend owner disagrees")
    return Cached, Method, Descriptor
