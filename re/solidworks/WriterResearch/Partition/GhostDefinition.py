# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Geometry.Parasolid import ParaWriteError, WritePointerMut, WriteSignedMut
from .PointRows import KPointSchema

# the pinned ghost reference registration files these eight actions
KGhostActions = (0, 0, 0, 0, 3, 6, 0, 0)

# the witnessed layout marks two entries in the logical owner roster
KGhostOwners = frozenset((0, 3))


# the named ghost type follows its schema with the observed registration fields
def EncodeGhostDef(DefinitionSlot: int, NameSlot: int, *, Schema: str) -> bytes:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost registration schema")
    if DefinitionSlot == NameSlot or not all(
        type(Index) is int and 0 < Index < 32767 for Index in (DefinitionSlot, NameSlot)
    ):
        raise ParaWriteError(
            "ghost registration requires distinct definition and name slots"
        )
    Result = bytearray()
    WriteSignedMut(Result, 2)  # two registered field types
    WritePointerMut(Result, DefinitionSlot)
    WritePointerMut(Result, 0)  # no following definition
    WritePointerMut(Result, NameSlot)
    WriteSignedMut(Result, 9000)
    Result.extend(KGhostActions)
    Result.append(0)  # no callback filed in this registration
    Result.extend(int(Index in KGhostOwners) for Index in range(18))
    Result.extend((9, 1))
    return bytes(Result)
