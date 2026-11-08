# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable, Mapping
from zipfile import ZipFile, ZipInfo

from convert.formats.Fusion.ZstdMember import ReadZstdMember


# design and history streams share the same bounded native zip decompression
def ReadFusionItem(
    DataValue: bytes,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Member: ZipInfo,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> bytes:
    if Member.compress_type == 93 and InflateZstd is not None:
        Central = getattr(Archive, "start_dir", None)
        if not isinstance(Central, int):
            raise ValueError("Missing Fusion ZIP central directory offset")
        Boundary = min(
            (
                Entry.header_offset
                for Entry in Members.values()
                if Entry.header_offset > Member.header_offset
            ),
            default=Central,
        )
        return ReadZstdMember(DataValue, Member, min(Boundary, Central), InflateZstd)
    if Member.compress_type not in (0, 8, 93):
        raise ValueError("Unsupported Fusion ZIP member compression")
    return Archive.read(Member)
