# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.OccurRecord import OccurRecord
from convert.formats.Fusion.Assembly.ComponentEntry import ComponentEntry
from convert.formats.Fusion.Assembly.AssemblyIndex import AssemblyIndex
from convert.formats.Fusion.Assembly.ComponentRead import (
    KComponentBase,
    KComponentGuid,
    ReadComponent,
)
from convert.formats.Fusion.Assembly.OccurCollection import (
    KOccurCollection,
    ReadOccurColl,
)
from convert.formats.Fusion.Assembly.OccurrenceRead import (
    KOccurrenceGuid,
    ReadOccurrence,
)
from convert.formats.Fusion.RecordSpan import RecordSpan

# unresolved assembly constraints can make saved matrices differ from solved placement
KConstraintGuids = frozenset(
    {
        "7F5A0426-1D2A-4DC4-9F06-58631F69D2F5",
        "AA8B3D40-B67D-4AF1-B3CF-E1E00279B5F0",
        "21E03EC1-0E53-406D-A852-6D088D4D1E95",
    }
)


# index typed native records once without deriving links from coincidental ids
def ReadAsmRecords(BulkData: bytes, Spans: tuple[RecordSpan, ...]) -> AssemblyIndex:
    PrimaryIds: set[int] = set()
    Components: dict[int, ComponentEntry] = {}
    Occurrences: dict[int, OccurRecord] = {}
    Collections: dict[int, tuple[int, tuple[int, ...]]] = {}
    HasConstraints = False
    for SpanValue in Spans:
        ObjectId, ClassGuid = SpanValue.ObjectId, SpanValue.ClassGuid
        if ClassGuid in KConstraintGuids:
            HasConstraints = True
        if ClassGuid == KComponentGuid and SpanValue.IsPrimary:
            if ObjectId in PrimaryIds:
                raise ValueError("Duplicate Fusion primary component")
            PrimaryIds.add(ObjectId)
            continue
        if ClassGuid not in (KComponentBase, KOccurrenceGuid, KOccurCollection):
            continue
        AddAsmRecordMut(BulkData, SpanValue, Components, Occurrences, Collections)
    CheckAsmIndex(Components, Occurrences, Collections, PrimaryIds, HasConstraints)
    return AssemblyIndex(Components, Occurrences, Collections)


# record type and ownership must agree before the corresponding index is populated
def AddAsmRecordMut(
    BulkData: bytes,
    SpanValue: RecordSpan,
    Components: dict[int, ComponentEntry],
    Occurrences: dict[int, OccurRecord],
    Collections: dict[int, tuple[int, tuple[int, ...]]],
) -> None:
    ObjectId, ClassGuid = SpanValue.ObjectId, SpanValue.ClassGuid
    Start = SpanValue.PayloadOffset
    if not 0 <= Start <= SpanValue.EndOffset <= len(BulkData):
        raise ValueError("Invalid Fusion assembly record bounds")
    if ClassGuid == KComponentBase:
        if SpanValue.IsPrimary or ObjectId in Components:
            raise ValueError("Ambiguous Fusion component continuation")
        Components[ObjectId] = ReadComponent(
            BulkData[Start + 4 : SpanValue.EndOffset], ObjectId
        )
    elif ClassGuid == KOccurrenceGuid:
        if not SpanValue.IsPrimary or ObjectId in Occurrences:
            raise ValueError("Ambiguous Fusion occurrence record")
        Occurrences[ObjectId] = ReadOccurrence(
            BulkData[Start : SpanValue.EndOffset], ObjectId
        )
    else:
        if not SpanValue.IsPrimary or ObjectId in Collections:
            raise ValueError("Ambiguous Fusion occurrence collection")
        Collections[ObjectId] = ReadOccurColl(BulkData[Start + 4 : SpanValue.EndOffset])


# cross record checks require the complete component and occurrence inventories
def CheckAsmIndex(
    Components: dict[int, ComponentEntry],
    Occurrences: dict[int, OccurRecord],
    Collections: dict[int, tuple[int, tuple[int, ...]]],
    PrimaryIds: set[int],
    HasConstraints: bool,
) -> None:
    if set(Components) != PrimaryIds and (Components or Occurrences or Collections):
        raise ValueError("Missing or mismatched Fusion component continuation")
    if HasConstraints and len(Occurrences) > 1:
        raise ValueError(
            "Fusion assembly contains unresolved joint or grounding records"
        )
