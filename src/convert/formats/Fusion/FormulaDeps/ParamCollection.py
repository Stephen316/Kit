# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# the native collection owns a named registry and typed parameter member references
KParamCollection = "B0556F58-EE09-46A7-B18F-E296F48E5B13"


# native member order is needed when verifying full parameter collection coverage
def ReadMemberOrder(
    BodyValue: bytes, ComponentId: int, *, VerifyOrder: bool = False
) -> tuple[int, tuple[int, ...]]:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(11) != bytes(11):
        raise ValueError("Unknown Fusion parameter collection header")
    StoredCount = Cursor.ReadWord()
    RegistryId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != b"\0":
        raise ValueError("Unknown Fusion parameter collection layout")
    Count = Cursor.ReadCount(100000)
    if len(BodyValue) != 42 + 11 * Count or (VerifyOrder and StoredCount != Count):
        raise ValueError("Invalid Fusion parameter collection extent")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if len(set(Members)) != Count or ReadNativeRef(Cursor) != ComponentId:
        raise ValueError("Invalid Fusion parameter collection membership")
    return RegistryId, Members


# callers that need only visibility can continue to use unordered member identities
def ReadCollection(BodyValue: bytes, ComponentId: int) -> tuple[int, frozenset[int]]:
    RegistryId, Members = ReadMemberOrder(BodyValue, ComponentId)
    return RegistryId, frozenset(Members)
