# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from struct import pack as PackBytes, pack_into as PackInto, unpack_from as UnpackFrom
from zipfile import ZIP_DEFLATED, ZipFile


def CodecFixture(Streams: dict[str, bytes], Version: int = 4) -> bytes:
    Buffer = BytesIO()
    with ZipFile(Buffer, "w", compression=ZIP_DEFLATED, compresslevel=0) as Archive:
        for StreamName, Payload in Streams.items():
            Archive.writestr(StreamName, Payload)
        Entries = Archive.infolist()
    Result = bytearray(Buffer.getvalue())
    Footer = len(Result) - 22
    Cursor = UnpackFrom("<I", Result, Footer + 16)[0]
    for Entry in Entries:
        LocalOffset = Entry.header_offset
        NameLength = UnpackFrom("<H", Result, LocalOffset + 26)[0]
        NameBytes = Entry.filename.encode("utf-8")
        Rotated = bytes(
            ((Value >> Version) | (Value << (8 - Version))) & 255 for Value in NameBytes
        )
        Result[LocalOffset : LocalOffset + 4] = bytes.fromhex("64d80045")
        PackInto("<H", Result, LocalOffset + 6, 6)
        Result[LocalOffset + 30 : LocalOffset + 30 + NameLength] = Rotated
        Result[Cursor : Cursor + 4] = bytes.fromhex("ae0d4ef6")
        PackInto("<H", Result, Cursor + 4, 0)
        PackInto("<H", Result, Cursor + 8, 6)
        Result[Cursor + 46 : Cursor + 46 + NameLength] = Rotated
        Cursor += 46 + NameLength
    Result[Footer : Footer + 4] = bytes.fromhex("54ce179a")
    return PackBytes(">II", 3966641030, Version) + Result
