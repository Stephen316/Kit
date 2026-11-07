# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid

# native body collections establish component scope through reciprocal membership
KBodyCollection = "CD57BC48-50EC-47DC-975A-FB6DEA72F4DA"

# the body and profile must agree on one typed component
KBodyComponent = "E03784ED-5E19-4E14-B9F2-3B07017018CD"


# body backlinks qualify membership without guessing from stored object numbers
def ReadBodyOwner(BulkData: bytes, Owners: dict[int, RecordSpan], BodyId: int) -> int:
    BodyCursor = SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    BodyCursor.Offset = len(BodyCursor.DataValue) - 11
    return ReadNativeRef(BodyCursor)


# every collected body must appear in both membership lists and point back to the collection
def ReadBodyList(
    BulkData: bytes, Owners: dict[int, RecordSpan], CollectionId: int
) -> tuple[tuple[int, ...], int]:
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KBodyCollection)
    if Cursor.TakeBytes(3) != bytes(3):
        raise ValueError("Unsupported Fusion body collection prefix")
    Cursor.TakeBytes(4)
    Count = Cursor.ReadCount(100000)
    RepeatAt = len(Cursor.DataValue) - 15 - 11 * Count
    if RepeatAt < Cursor.Offset + 11 * Count:
        raise ValueError("Truncated Fusion body collection membership")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    Cursor.Offset = RepeatAt
    if (
        len(set(Members)) != Count
        or Cursor.ReadWord() != Count
        or tuple(ReadNativeRef(Cursor) for _ in range(Count)) != Members
    ):
        raise ValueError("Fusion body collection repeated membership disagrees")
    ComponentId = ReadNativeRef(Cursor)
    SelectCursor(BulkData, Owners, ComponentId, KBodyComponent)
    if any(
        ReadBodyOwner(BulkData, Owners, BodyId) != CollectionId for BodyId in Members
    ):
        raise ValueError("Fusion body collection ownership disagrees")
    return Members, ComponentId
