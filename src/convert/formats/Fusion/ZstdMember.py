# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from struct import unpack_from as UnpackFrom
from zipfile import ZipInfo
from zlib import crc32 as CrcValue


# older zip readers need a bounded local entry before using an external zstandard codec
def ReadZstdMember(
    DataValue: bytes,
    Member: ZipInfo,
    Boundary: int,
    Inflate: Callable[[bytes, int], bytes],
) -> bytes:
    Offset = Member.header_offset
    if not 0 <= Offset <= Boundary - 30 <= len(DataValue) - 30:
        raise ValueError("Invalid Fusion ZIP local header extent")
    Magic, _, Flags, Method, _, _, _, _, _, NameSize, ExtraSize = UnpackFrom(
        "<4s5H3I2H", DataValue, Offset
    )
    NameStart = Offset + 30
    NameFinish = NameStart + NameSize
    DataStart = NameFinish + ExtraSize
    DataFinish = DataStart + Member.compress_size
    if (
        Magic != b"PK\x03\x04"
        or Flags != Member.flag_bits
        or Method != Member.compress_type
        or DataFinish > Boundary
    ):
        raise ValueError("Fusion ZIP local and central entries disagree")
    NameValue = DataValue[NameStart:NameFinish].decode(
        "utf-8" if Flags & 0x800 else "cp437"
    )
    if NameValue != Member.orig_filename:
        raise ValueError("Fusion ZIP local member name differs")
    Result = Inflate(DataValue[DataStart:DataFinish], Member.file_size)
    if len(Result) != Member.file_size or CrcValue(Result) != Member.CRC:
        raise ValueError("Fusion ZIP member size or CRC mismatch")
    return Result
