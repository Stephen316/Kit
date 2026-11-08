# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from re import compile as CompilePattern

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid
from convert.formats.Fusion.Topology.BodyCollection import ReadBodyOwner
from convert.formats.Fusion.Topology.BodyCollectionRole import KBodyHistory
from convert.formats.Fusion.Topology.CurrentBodyCollection import ReadCurrentBody

# only the basename of a native history stream can enter the same asset lookup
KAsmName = CompilePattern(
    r"BREP\.[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.smbh"
)


# local asm handles are scoped by the explicit native history member
@MakeDataClass(frozen=True, slots=True)
class BodyAsmRef:
    RecordId: int
    FileName: str
    Handle: int
    Handles: frozenset[int]


# opaque body handles include zero and remain unique within their exact mapping
def ReadAsmMapRow(
    BulkData: bytes, Owners: dict[int, RecordSpan], Identity: int
) -> tuple[int, dict[int, int], str]:
    Cursor = SelectCursor(BulkData, Owners, Identity, KBodyHistory)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body history mapping prefix")
    Count = Cursor.ReadCount(1024)
    Entries = tuple((Cursor.ReadLong(), Cursor.ReadLong()) for _ in range(Count))
    Collection = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion body history mapping separator")
    NameValue = Cursor.ReadText(WideText=True, Maximum=64)
    if (
        Cursor.Offset != len(Cursor.DataValue)
        or (bool(Entries) and KAsmName.fullmatch(NameValue) is None)
        or (not Entries and NameValue)
        or len({Handle for Handle, _ in Entries}) != Count
        or len({BodyId for _, BodyId in Entries}) != Count
        or any(
            Owners.get(BodyId) is None or Owners[BodyId].ClassGuid != KBodyGuid
            for _, BodyId in Entries
        )
    ):
        raise ValueError("Fusion body history mapping is malformed or ambiguous")
    return Collection, {BodyId: Handle for Handle, BodyId in Entries}, NameValue


# reciprocal body collection membership prevents a same named handle in another component
def ReadBodyAsmRef(
    BulkData: bytes, Owners: dict[int, RecordSpan], BodyId: int, Component: int
) -> BodyAsmRef:
    Collection = ReadBodyOwner(BulkData, Owners, BodyId)
    Members, BackendId = ReadCurrentBody(BulkData, Owners, Collection, Component)
    Owner, Entries, FileName = ReadAsmMapRow(BulkData, Owners, BackendId)
    if (
        Owner != Collection
        or Entries.keys() != frozenset(Members)
        or BodyId not in Entries
    ):
        raise ValueError("Fusion body history mapping disagrees with its component")
    return BodyAsmRef(BackendId, FileName, Entries[BodyId], frozenset(Entries.values()))
