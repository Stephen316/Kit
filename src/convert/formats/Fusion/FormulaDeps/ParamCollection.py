# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# the native collection owns a named registry and typed parameter member references
KParamCollection = "B0556F58-EE09-46A7-B18F-E296F48E5B13"


# only complete collections can establish which names are visible to formulas
def ReadCollection(BodyValue: bytes, ComponentId: int) -> tuple[int, frozenset[int]]:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(11) != bytes(11):
        raise ValueError("Unknown Fusion parameter collection header")
    Cursor.ReadWord()
    RegistryId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != b"\0":
        raise ValueError("Unknown Fusion parameter collection layout")
    Count = Cursor.ReadCount(100000)
    if len(BodyValue) != 42 + 11 * Count:
        raise ValueError("Invalid Fusion parameter collection extent")
    Members = frozenset(ReadNativeRef(Cursor) for _ in range(Count))
    if len(Members) != Count or ReadNativeRef(Cursor) != ComponentId:
        raise ValueError("Invalid Fusion parameter collection membership")
    return RegistryId, Members
