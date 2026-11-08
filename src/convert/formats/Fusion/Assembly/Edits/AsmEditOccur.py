# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose

from convert.formats.Fusion.Assembly.ComponentRead import ReadComponent

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.EditBookkeep import CheckEditBook
from convert.formats.Fusion.Assembly.OccurCollection import (
    KOccurCollection,
    ReadOccurColl,
)
from convert.formats.Fusion.Assembly.OccurRecord import OccurRecord
from convert.formats.Fusion.Assembly.OccurrenceRead import (
    KOccurrenceGuid,
    ReadOccurrence,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor

# the occurrence datum is neither a body selection nor a generic dependency
KEditOccurDatum = "2D6E13A1-BBEF-4FB3-9277-00D99F634136"


# matrix comparisons keep local distances distinct from occurrence world paths
def HasSameMatrix(First: tuple[float, ...], Second: tuple[float, ...]) -> bool:
    return len(First) == len(Second) == 16 and all(
        IsClose(Actual, Expected, abs_tol=1e-9, rel_tol=0.0)
        for Actual, Expected in zip(First, Second)
    )


# the current graph and native collection must agree on a real local occurrence
def ReadEditOccur(
    BulkData: bytes, IndexValue: AsmEditIndex, OccurrenceId: int
) -> OccurRecord:
    Instance = IndexValue.Occurrences.get(OccurrenceId)
    if Instance is None:
        raise ValueError("Fusion edit occurrence is absent from the current assembly")
    Owners = IndexValue.Owners
    SpanValue = Owners.get(OccurrenceId)
    if SpanValue is None or SpanValue.ClassGuid != KOccurrenceGuid:
        raise ValueError("Missing typed Fusion edit occurrence")
    Record = ReadOccurrence(
        BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset], OccurrenceId
    )
    if (
        Record.CollectionId is None
        or Record.ComponentId != IndexValue.Components.get(Instance.definition_id)
        or Record.NativeGuid != Instance.attributes.get("fusion.native_guid")
        or not HasSameMatrix(
            tuple(
                Value * 10.0 if Offset in (3, 7, 11) else Value
                for Offset, Value in enumerate(Record.Transform)
            ),
            Instance.transform.values,
        )
    ):
        raise ValueError("Fusion edit occurrence definition or transform disagrees")
    Collection = SelectCursor(BulkData, Owners, Record.CollectionId, KOccurCollection)
    OwnerId, Members = ReadOccurColl(Collection.DataValue)
    if (
        OwnerId != IndexValue.Components.get(Instance.owner_definition_id)
        or not 0 <= Instance.order < len(Members)
        or Members[Instance.order] != OccurrenceId
    ):
        raise ValueError("Fusion edit occurrence collection membership disagrees")
    ParentSpan = IndexValue.ComponentSpans.get(OwnerId)
    if (
        ParentSpan is None
        or ReadComponent(
            BulkData[ParentSpan.PayloadOffset + 4 : ParentSpan.EndOffset], OwnerId
        ).CollectionId
        != Record.CollectionId
    ):
        raise ValueError("Fusion edit occurrence parent collection is not reciprocal")
    return Record


# the datum identifies its placement receiver through reciprocal bookkeeping
def ReadEditDatum(
    BulkData: bytes, IndexValue: AsmEditIndex, DatumId: int, OwnerId: int
) -> OccurRecord:
    Cursor = SelectCursor(BulkData, IndexValue.Owners, DatumId, KEditOccurDatum)
    if len(Cursor.DataValue) != 39 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion assembly edit occurrence datum")
    OccurrenceId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion assembly edit datum context")
    BookId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1) or ReadNativeRef(Cursor) != OwnerId:
        raise ValueError("Fusion assembly edit datum owner disagrees")
    CheckEditBook(BulkData, IndexValue, BookId, DatumId, 0)
    return ReadEditOccur(BulkData, IndexValue, OccurrenceId)
