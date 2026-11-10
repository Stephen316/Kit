# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO
from struct import pack as PackValue

# the standard raw block bound keeps each generated frame portable
KRawBlockSize = 128 * 1024

# the magic word identifies the frame independently of the outer zip method
KZstdMagic = b"\x28\xb5\x2f\xfd"


# single segment frames serve small entries and a fixed window bounds larger entries
def ZstdFrameHead(DataSize: int) -> bytes:
    if DataSize < 256:
        return KZstdMagic + PackValue("<BB", 0x20, DataSize)
    if DataSize < 256 + (1 << 16):
        return KZstdMagic + PackValue("<BH", 0x60, DataSize - 256)
    if DataSize <= KRawBlockSize:
        return KZstdMagic + PackValue("<BI", 0xA0, DataSize)
    return KZstdMagic + PackValue("<BBI", 0x80, 0x38, DataSize)


# the enclosing header needs an exact frame size before writing any data
def ZstdFrameSize(DataSize: int) -> int:
    Blocks = max(1, (DataSize + KRawBlockSize - 1) // KRawBlockSize)
    return len(ZstdFrameHead(DataSize)) + Blocks * 3 + DataSize


# independent raw blocks avoid a compressor dependency or a second payload copy
def WriteZstdMut(Output: BytesIO, DataValue: bytes) -> None:
    DataSize = len(DataValue)
    _ = Output.write(ZstdFrameHead(DataSize))
    ViewValue = memoryview(DataValue)
    for Offset in range(0, max(1, DataSize), KRawBlockSize):
        Finish = min(Offset + KRawBlockSize, DataSize)
        Header = ((Finish - Offset) << 3) | (Finish == DataSize)
        _ = Output.write(Header.to_bytes(3, "little"))
        _ = Output.write(ViewValue[Offset:Finish])
