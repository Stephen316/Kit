# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import NamedTuple

from convert.Geometry.Parasolid import (
    ParaWriteError,
    WritePointerMut,
    WriteSignedMut,
    WriteTagMut,
)
from .GhostSchemas import WritePrimitiveField
from .PointRows import KPointSchema
from .WorldRow import WriteRefField

# the first array has twenty slots and one occupied ghost attribute reference
KGhostCapacity = 20


# a body list and pointer array own their distinct transport slots
class GhostListOwner(NamedTuple):
    body: int
    attribute: int
    list_slot: int
    array_slot: int


# list and array records file at different positions in the ghost partition
class GhostListRecords(NamedTuple):
    body_list: bytes
    pointer_array: bytes


# the first body list files these named fields before its node
def WriteListSchema(Result: bytearray) -> None:
    Result.append(11)
    Result.extend(b"C")
    WritePrimitiveField(Result, "I", "list_type", 1, "u")
    WritePrimitiveField(Result, "I", "notransmit", 1, "l")
    Result.extend(b"CCCDCCD")
    WritePrimitiveField(Result, "I", "finger_index", 1, "d")
    WriteRefField(Result, "I", "finger_block", 1012)
    Result.extend(b"CZ")


# the first pointer array files an explicit index offset field
def WriteArraySchema(Result: bytearray) -> None:
    Result.append(4)
    Result.extend(b"C")
    WritePrimitiveField(Result, "I", "index_map_offset", 1, "d")
    Result.extend(b"CCZ")


# one list binds one owned body and points at both ends of its single array
def EncodeBodyList(Owner: GhostListOwner, First: bool) -> bytes:
    Result = bytearray()
    WriteTagMut(Result, 70)
    if First:
        WriteListSchema(Result)
    WritePointerMut(Result, Owner.list_slot)
    WriteSignedMut(Result, 0)
    Result.extend((4, 1))  # measured list type and notransmit flag
    for Value in (Owner.body, 0, 0):
        WritePointerMut(Result, Value)
    for Value in (1, KGhostCapacity, 1):
        WriteSignedMut(Result, Value)
    WritePointerMut(Result, Owner.array_slot)
    WritePointerMut(Result, Owner.array_slot)
    return bytes(Result)


# the array retains its one attribute and clears every unused entry
def EncodePointerArray(Owner: GhostListOwner, First: bool) -> bytes:
    Result = bytearray()
    WriteTagMut(Result, 74)
    if First:
        WriteArraySchema(Result)
    WriteSignedMut(Result, KGhostCapacity)
    WritePointerMut(Result, Owner.array_slot)
    WriteSignedMut(Result, 1)
    WriteSignedMut(Result, 0)  # absent index map offset
    WritePointerMut(Result, 0)
    WritePointerMut(Result, Owner.attribute)
    for _ in range(KGhostCapacity - 1):
        WritePointerMut(Result, 0)
    return bytes(Result)


# the two independent class occurrence flags follow the caller filing order
def EncodeGhostLists(
    Owner: GhostListOwner, *, Schema: str, FirstList: bool, FirstArray: bool
) -> GhostListRecords:
    if (
        Schema != KPointSchema
        or type(FirstList) is not bool
        or type(FirstArray) is not bool
    ):
        raise ParaWriteError("unsupported ghost list framing")
    if len(set(Owner)) != 4 or not all(
        type(Index) is int and 0 < Index < 32767 for Index in Owner
    ):
        raise ParaWriteError("ghost list requires distinct owner and transport slots")
    return GhostListRecords(
        EncodeBodyList(Owner, FirstList), EncodePointerArray(Owner, FirstArray)
    )
