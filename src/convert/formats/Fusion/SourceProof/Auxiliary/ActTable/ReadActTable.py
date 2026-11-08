# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActCursor import ActCursor
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActKeys import ReadActKeysMut
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRoutes import (
    ReadActRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActTable import ActTable
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActTokens import (
    ReadActRolesMut,
    ReadActUuidMut,
)

# the registered table class distinguishes its keys from all other act records
KActTableGuid = "8EF12734-4D22-4F6A-8A80-1462E6B40A13"


# route consumers need all references and role tokens validated against their native index
def ReadActTable(ActData: bytes, ActSpans: tuple[RecordSpan, ...]) -> ActTable:
    Tables = tuple(
        EntrySpan for EntrySpan in ActSpans if EntrySpan.ClassGuid == KActTableGuid
    )
    if len(Tables) != 1 or Tables[0].ObjectId != 0:
        raise ValueError("Missing or ambiguous Fusion ACT table")
    (TableSpan,) = Tables
    Cursor = ActCursor(ActData, TableSpan)
    if Cursor.ReadText(Maximum=8) != "ACTTable" or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion ACT table preamble")
    Entries = ReadActKeysMut(Cursor)
    SnapshotId, HeadId = ReadActUuidMut(Cursor), ReadActUuidMut(Cursor)
    if SnapshotId == HeadId or Cursor.TakeBytes(4) != bytes(4):
        raise ValueError("Invalid Fusion ACT table identifiers")
    Roles = ReadActRolesMut(Cursor)
    if (
        len(Roles) != len(ActRole)
        or HeadId not in {Token for _, Token in Roles}
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError("Invalid Fusion ACT table roles or extent")
    Routes = ReadActRoutes(ActData, ActSpans, Entries)
    return ActTable(SnapshotId, HeadId, TableSpan, Routes, Roles)
