# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from zipfile import ZipInfo


# inspect central metadata before inflating either design stream
def IndexZipItems(Entries: list[ZipInfo]) -> dict[str, ZipInfo]:
    if not Entries or len(Entries) > 4096:
        raise ValueError("Fusion ZIP entry count exceeds limit")
    Members: dict[str, ZipInfo] = {}
    Offsets: set[int] = set()
    TotalSize = 0
    for Entry in Entries:
        if (
            Entry.filename != Entry.orig_filename
            or Entry.filename in Members
            or Entry.header_offset in Offsets
        ):
            raise ValueError("Invalid or duplicate Fusion ZIP member")
        if Entry.flag_bits & 1:
            raise ValueError("Encrypted Fusion ZIP member")
        if max(Entry.file_size, Entry.compress_size) > 64 * 1024 * 1024:
            raise ValueError("Fusion ZIP member exceeds size limit")
        TotalSize += Entry.file_size
        if TotalSize > 128 * 1024 * 1024:
            raise ValueError("Fusion ZIP declared size exceeds limit")
        Members[Entry.filename] = Entry
        Offsets.add(Entry.header_offset)
    return Members
