# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.Assembly.Solids.ScopeGraph import ReadScopeGraph
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# scope records identify a definition and optionally the occurrence creation snapshot
KScopeGuid = "5D15E992-1E93-4D79-A553-10D2624148AE"

# bookkeeping verifies scope record ownership without interpreting its timestamp
KScopeOwner = "6CCF41D5-40BE-48ED-A834-18F3EAED6C57"

# the related record must be a typed snapshot before it can qualify an occurrence
KScopeSnapshot = "54F9ACE8-B5B8-4A6E-B582-64F629511DE4"


# component identity remains separate from the optional creation event
@Dataclass(frozen=True, slots=True)
class CreatorScope:
    ScopeId: int
    ComponentId: int
    SnapshotId: int | None


# bounded scope references corroborate the definition and exact snapshot type
def ReadOwnerScope(
    BulkData: bytes, Owners: dict[int, RecordSpan], Identity: int
) -> CreatorScope:
    Cursor = SelectCursor(BulkData, Owners, Identity, KScopeGuid)
    if Cursor.TakeBytes(3) != b"\0\0\1":
        raise ValueError("Unsupported Fusion creator scope prefix")
    ComponentId = ReadNativeRef(Cursor)
    _ = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
    if Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion creator scope framing")
    Owner = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KScopeOwner)
    if (
        len(Owner.DataValue) != 39
        or Owner.TakeBytes(12) != bytes(12)
        or ReadNativeRef(Owner) != Identity
    ):
        raise ValueError("Fusion creator scope bookkeeping disagrees")
    SnapshotId = ReadOptRefMut(Cursor)
    if SnapshotId is not None:
        _ = SelectCursor(BulkData, Owners, SnapshotId, KScopeSnapshot)
    if Cursor.TakeBytes(1) != bytes(1) or Cursor.Offset != len(Cursor.DataValue):
        raise ValueError("Unsupported Fusion creator scope suffix")
    return CreatorScope(Identity, ComponentId, SnapshotId)


# unique observed scope edges keep each modeling feature in its native definition
def ReadAsmScopes(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    FeatureIds: frozenset[int],
) -> dict[int, CreatorScope]:
    Scopes: dict[int, CreatorScope] = {}
    Decoded: dict[int, CreatorScope] = {}
    for (Source, Target, Flags), Count in ReadScopeGraph(
        BulkData, Owners, OwnerId
    ).items():
        if (
            Source not in FeatureIds
            or Flags != 4096
            or Owners[Target].ClassGuid != KScopeGuid
        ):
            continue
        if Source in Scopes or Count != 1:
            raise ValueError("Ambiguous Fusion creator component scope")
        if Target not in Decoded:
            Decoded[Target] = ReadOwnerScope(BulkData, Owners, Target)
        Scopes[Source] = Decoded[Target]
    return Scopes
