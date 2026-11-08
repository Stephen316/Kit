# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from uuid import UUID

from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# native change tokens need an unambiguous spelling for exact snapshot comparisons
def EmitActUuidMut(SinkValue: MetaSink, TokenText: str) -> None:
    if type(TokenText) is not str or len(TokenText) != 36:
        raise ValueError("Invalid Fusion ACT token")
    TokenValue = UUID(TokenText)
    if TokenValue.int == 0 or str(TokenValue) != TokenText:
        raise ValueError("Noncanonical Fusion ACT token")
    SinkValue.AddText(TokenText, WideText=True)


# ordered typed role names prevent competing values for the same change token
def EmitActRolesMut(
    SinkValue: MetaSink, Roles: tuple[tuple[ActRole, str], ...]
) -> None:
    SinkValue.AddCount(Roles, len(ActRole))
    if not Roles:
        raise ValueError("Fusion ACT record has no roles")
    LastName = ""
    for RoleRow in Roles:
        if type(RoleRow) is not tuple or len(RoleRow) != 2:
            raise ValueError("Invalid Fusion ACT role row")
        RoleValue, TokenText = RoleRow
        if not isinstance(RoleValue, ActRole) or RoleValue.value <= LastName:
            raise ValueError("Invalid or unordered Fusion ACT roles")
        SinkValue.AddText(RoleValue.value)
        EmitActUuidMut(SinkValue, TokenText)
        LastName = RoleValue.value
