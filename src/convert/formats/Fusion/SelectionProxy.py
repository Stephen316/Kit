# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs

# registered identities keep entity selections distinct from sketch and boundary representation leaves
KSelectProxy = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"


# a typed primary record bounds every part of a selection chain
def SelectCursor(
    BulkData: bytes, Owners: dict[int, RecordSpan], Identity: int, ClassGuid: str
) -> MetaCursor:
    SpanValue = Owners.get(Identity)
    if SpanValue is None or SpanValue.ClassGuid != ClassGuid:
        raise ValueError("Missing typed Fusion selection record")
    return MetaCursor(BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset])


# one owned proxy yields an exact descriptor without scanning the archive
def ReadSelectDesc(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> int:
    Cursor = SelectCursor(BulkData, Owners, SelectId, KSelectProxy)
    Prefix = Cursor.DataValue[:2]
    if Prefix == b"\0\1":
        ReadGeomAttrs(Cursor)
    elif Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion selection proxy prefix")
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion selection proxy count")
    Descriptor = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion secondary selection prefix")
    if Cursor.ReadCount(1):
        ReadNativeRef(Cursor)
    Cursor.TakeBytes(60)
    if ReadNativeRef(Cursor) != FeatureId or Cursor.Offset != len(Cursor.DataValue):
        raise ValueError("Fusion selection proxy owner or width disagrees")
    return Descriptor
