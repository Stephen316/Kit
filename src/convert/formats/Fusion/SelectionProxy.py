# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


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


# selection proxies retain the same framing for individual and counted operands
def ReadSelectIds(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SelectId: int,
    FeatureId: int,
    Maximum: int,
) -> tuple[tuple[int, ...], dict[str, int | float]]:
    Cursor = SelectCursor(BulkData, Owners, SelectId, KSelectProxy)
    Prefix = Cursor.DataValue[:2]
    Attributes: dict[str, int | float] = {}
    if Prefix == b"\0\1":
        Attributes = ReadGeomAttrs(Cursor)
    elif Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion selection proxy prefix")
    Count = Cursor.ReadWord()
    if not 1 <= Count <= Maximum:
        raise ValueError("Unsupported Fusion selection proxy count")
    Descriptors = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion secondary selection prefix")
    if Cursor.ReadCount(1):
        _ = ReadNativeRef(Cursor)
    _ = Cursor.TakeBytes(60)
    if ReadNativeRef(Cursor) != FeatureId or Cursor.Offset != len(Cursor.DataValue):
        raise ValueError("Fusion selection proxy owner or width disagrees")
    return Descriptors, Attributes


# the established single selection api keeps its exact cardinality and owner checks
def ReadSelectDesc(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> int:
    (Descriptor,), _ = ReadSelectIds(BulkData, Owners, SelectId, FeatureId, 1)
    return Descriptor


# feature owned attributes can corroborate role controls without altering descriptor order
def ReadSelectList(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> tuple[tuple[int, ...], dict[str, int | float]]:
    Descriptors, Attributes = ReadSelectIds(BulkData, Owners, SelectId, FeatureId, 1024)
    if len(set(Descriptors)) != len(Descriptors) or any(
        Identity not in Owners for Identity in Descriptors
    ):
        raise ValueError("Fusion selection proxy descriptors are missing or repeated")
    return Descriptors, Attributes


# callers without proxy attribute semantics can request just the ordered native descriptors
def ReadSelectDescs(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> tuple[int, ...]:
    Descriptors, _ = ReadSelectList(BulkData, Owners, SelectId, FeatureId)
    return Descriptors
