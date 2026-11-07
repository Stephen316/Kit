# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from uuid import UUID

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectDesc, SelectCursor

# construction entities use the shared selection descriptor
KSelectDesc = "5A1BF548-241F-46FD-9FB5-E4B05126EB9D"

# the entity leaf contains an object identity rather than a sketch tag or topology recipe
KSelectLeaf = "90055C05-546C-4EE7-B3C9-3DD922AD0C9C"


# bounded uuid text validates the native selection namespace framing
def ReadSelectUuid(Cursor: MetaCursor) -> str:
    GuidText = Cursor.ReadText(True, Maximum=36)
    if len(GuidText) != 36:
        raise ValueError("Unsupported Fusion selection GUID")
    UUID(GuidText)
    return GuidText


# sketch and construction selections share a descriptor and reciprocal feature owner
def ReadSelectLeaf(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> tuple[int, int]:
    Descriptor = ReadSelectDesc(BulkData, Owners, SelectId, FeatureId)
    return Descriptor, ReadDescLeaf(BulkData, Owners, Descriptor, FeatureId)


# dispatchers that already classified a descriptor reuse its bounded leaf reader
def ReadDescLeaf(
    BulkData: bytes, Owners: dict[int, RecordSpan], Descriptor: int, FeatureId: int
) -> int:
    Cursor = SelectCursor(BulkData, Owners, Descriptor, KSelectDesc)
    if len(Cursor.DataValue) != 263 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion entity selection descriptor")
    Terminal = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion entity selection namespace count")
    ReadSelectUuid(Cursor)
    ReadSelectUuid(Cursor)
    Cursor.Offset = 252
    if ReadNativeRef(Cursor) != FeatureId:
        raise ValueError("Fusion entity selection descriptor owner disagrees")
    return Terminal


# the construction leaf addresses the native object directly
def ReadEntityLeaf(
    BulkData: bytes, Owners: dict[int, RecordSpan], Terminal: int
) -> int:
    Cursor = SelectCursor(BulkData, Owners, Terminal, KSelectLeaf)
    if len(Cursor.DataValue) != 10 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion entity selection leaf")
    return Cursor.ReadLong()


# callers selecting a construction entity can resolve the complete chain at once
def ReadEntityRef(
    BulkData: bytes, Owners: dict[int, RecordSpan], SelectId: int, FeatureId: int
) -> tuple[int, int, int]:
    Descriptor, Terminal = ReadSelectLeaf(BulkData, Owners, SelectId, FeatureId)
    return Descriptor, Terminal, ReadEntityLeaf(BulkData, Owners, Terminal)
