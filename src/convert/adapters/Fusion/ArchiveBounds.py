# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from struct import unpack_from as UnpackFrom
from typing import BinaryIO

# the native reader applies this input ceiling to active design archives
KArchiveLimit = 128 * 1024 * 1024

# central metadata stays bounded before the standard library allocates entry objects
KCentralLimit = 4 * 1024 * 1024

# the longest comment and an optional zip locator fit in one tail window
KFooterWindow = 22 + 65535 + 20


# conventional single disk footer fields bound standard library metadata reads
def CheckZipTailMut(Handle: BinaryIO, StartOffset: int) -> int:
    EndOffset = Handle.seek(0, 2)
    SizeValue = EndOffset - StartOffset
    if not 22 <= SizeValue <= KArchiveLimit:
        raise ValueError("Fusion ZIP size is outside the supported range")
    TailSize = min(SizeValue, KFooterWindow)
    Handle.seek(EndOffset - TailSize)
    TailBytes = Handle.read(TailSize)
    Footer = TailBytes.rfind(b"PK\x05\x06")
    if Footer < 0 or Footer + 22 > len(TailBytes):
        raise ValueError("Missing Fusion ZIP central directory footer")
    (
        DiskIndex,
        CentralDisk,
        DiskCount,
        TotalCount,
        CentralSize,
        CentralOffset,
        CommentSize,
    ) = UnpackFrom("<4H2IH", TailBytes, Footer + 4)
    if (
        DiskIndex != 0
        or CentralDisk != 0
        or not 0 < DiskCount == TotalCount <= 4096
        or not 46 * TotalCount <= CentralSize <= KCentralLimit
        or CentralOffset + CentralSize > SizeValue - TailSize + Footer
        or Footer + 22 + CommentSize != len(TailBytes)
        or (Footer >= 20 and TailBytes[Footer - 20 : Footer - 16] == b"PK\x06\x07")
    ):
        raise ValueError("Unsupported Fusion ZIP central directory bounds")
    return TotalCount
