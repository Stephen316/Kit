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


# all selected streams use the same bounded native and supplied codec checks
def ReadFusionItem(
    DataValue: bytes,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Member: ZipInfo,
    InflateZstd: Callable[[bytes, int], bytes] | None,
    *,
    Boundary: int | None = None,
) -> bytes:
    if Member.compress_type == 93 and InflateZstd is not None:
        if Boundary is None:
            Central = getattr(Archive, "start_dir", None)
            if not isinstance(Central, int):
                raise ValueError("Missing Fusion ZIP central directory offset")
            Boundary = min(
                (
                    Entry.header_offset
                    for Entry in Members.values()
                    if Member.header_offset < Entry.header_offset < Central
                ),
                default=Central,
            )
        return ReadZstdMember(DataValue, Member, Boundary, InflateZstd)
    if Member.compress_type not in (0, 8, 93):
        raise ValueError("Unsupported Fusion ZIP member compression")
    return Archive.read(Member)
