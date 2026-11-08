# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from uuid import UUID

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# canonical tokens prevent alternate spellings from entering exact revision joins
def ReadActUuidMut(Cursor: MetaCursor) -> str:
    GuidText = Cursor.ReadText(True, Maximum=36)
    GuidValue = UUID(GuidText)
    if GuidValue.int == 0 or str(GuidValue) != GuidText:
        raise ValueError("Noncanonical Fusion ACT token")
    return GuidText


# closed role vocabulary and ordered names make token maps unambiguous
def ReadActRolesMut(Cursor: MetaCursor) -> tuple[tuple[ActRole, str], ...]:
    Roles = tuple(
        (ActRole(Cursor.ReadText(Maximum=16)), ReadActUuidMut(Cursor))
        for _ in range(Cursor.ReadCount(len(ActRole)))
    )
    RoleNames = tuple(NameValue for NameValue, _ in Roles)
    if not RoleNames or RoleNames != tuple(sorted(set(RoleNames))):
        raise ValueError("Invalid or unordered Fusion ACT roles")
    return Roles
