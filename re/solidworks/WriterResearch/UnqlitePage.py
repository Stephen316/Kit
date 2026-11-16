# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write a fresh one-bucket UnQLite database from bounded key and value records."""

from collections.abc import Sequence
from datetime import datetime
from struct import Struct, pack

KPageSize = 4096
KSectorSize = 512
KStorage = b"hash"
KSignature = b"unqlite"
KDatabaseMagic = 0xDB7C2712
KBucketMagic = 0xFA782DCB
KHashWord = b"chm@symisc"
KBucketHeader = Struct(">HHQ")
KCellHeader = Struct(">IIQHQ")
KFreeHeader = Struct(">HH")


# the database and each cell use the same public UnQLite hash function
def KeyHash(Key: bytes) -> int:
    Value = 5381
    for Byte in Key[:2048]:
        Value = (Value * 33 + Byte) & 0xFFFFFFFF
    return Value


# UnQLite stores a wall clock with two second precision in its database header
def DosClock(Created: datetime) -> int:
    if Created.tzinfo is not None or not 1980 <= Created.year <= 2107:
        raise ValueError("UnQLite creation clock must be a DOS-range local wall time")
    return (
        (Created.year - 1980) << 25
        | Created.month << 21
        | Created.day << 16
        | Created.hour << 11
        | Created.minute << 5
        | Created.second // 2
    )


# fresh single-bucket pages contain consecutive local cells and one tail free block
def WriteBucket(Records: Sequence[tuple[bytes, bytes]]) -> bytes:
    Page = bytearray(KPageSize)
    Offset = KBucketHeader.size
    Previous = 0
    Keys = set()
    for Key, Value in Records:
        if (
            not isinstance(Key, bytes)
            or not isinstance(Value, bytes)
            or not Key
            or Key in Keys
        ):
            raise ValueError("UnQLite bucket needs distinct nonempty byte keys")
        CellSize = KCellHeader.size + len(Key) + len(Value)
        End = Offset + CellSize
        if CellSize >= KPageSize // 2 or End + KFreeHeader.size > KPageSize:
            raise ValueError("record needs a larger or overflow UnQLite bucket")
        KCellHeader.pack_into(
            Page, Offset, KeyHash(Key), len(Key), len(Value), Previous, 0
        )
        Page[Offset + KCellHeader.size : End] = Key + Value
        Keys.add(Key)
        Previous, Offset = Offset, End
    if not Keys:
        raise ValueError("a fresh populated UnQLite bucket needs at least one record")
    KBucketHeader.pack_into(Page, 0, Previous, Offset, 0)
    KFreeHeader.pack_into(Page, Offset, 0, KPageSize - Offset)
    return bytes(Page)


# the pager maps logical bucket zero directly to physical page two
def WriteSingleBucket(
    Created: datetime, Records: Sequence[tuple[bytes, bytes]]
) -> bytes:
    Database = (
        KSignature
        + pack(
            ">IIIIH",
            KDatabaseMagic,
            DosClock(Created),
            KSectorSize,
            KPageSize,
            len(KStorage),
        )
        + KStorage
    )
    Buckets = pack(">IIQQQQIQQ", KBucketMagic, KeyHash(KHashWord), 0, 0, 1, 0, 1, 0, 2)
    return (
        Database.ljust(KPageSize, b"\0")
        + Buckets.ljust(KPageSize, b"\0")
        + WriteBucket(Records)
    )
