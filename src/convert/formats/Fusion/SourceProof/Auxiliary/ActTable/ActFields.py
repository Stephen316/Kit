# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActCursor import ActCursor
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActTokens import (
    ReadActRolesMut,
)

# fields records have their own registered wire class in the active act segment
KActFieldsGuid = "ABC8C0E3-50FB-4E8C-AFF3-116759A36073"


# a repeated key binds the role tokens to their exact table row
def ReadActFields(
    ActData: bytes, FieldsSpan: RecordSpan, KeyValue: str
) -> tuple[tuple[tuple[ActRole, str], ...], int]:
    Cursor = ActCursor(ActData, FieldsSpan)
    if Cursor.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion ACT fields preamble")
    Roles = ReadActRolesMut(Cursor)
    if Cursor.ReadText(True, Maximum=22) != KeyValue:
        raise ValueError("Fusion ACT field route key disagrees")
    Residual = len(Cursor.DataValue) - Cursor.Offset
    if Residual and (Residual != 2 or FieldsSpan.EndOffset != len(ActData)):
        raise ValueError("Unsupported Fusion ACT fields extent")
    return Roles, Residual
