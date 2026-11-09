# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import unpack_from as UnpackFrom
from convert.adapters.solidworks.container.DecodeName import DecodeName
from convert.adapters.solidworks.container.DecodePayload import DecodePayload
from convert.adapters.solidworks.container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.container.StreamRecord import StreamRecord
from convert.adapters.solidworks.container.StreamLimits import (
    KMaxNameBytes,
    KMaxUncompressedStream,
)


def DecodeScanned(
    BlobValue: bytes,
    Offset: int,
    Signature: bytes,
    SizeLimit: int = KMaxUncompressedStream,
) -> StreamRecord | None:
    HeaderOffset = Offset + len(Signature)
    if HeaderOffset + 16 > len(BlobValue):
        return None
    CrcThreeTwoValue, CompressedSize, UncompressedSize, NameSize = UnpackFrom(
        "<IIII", BlobValue, HeaderOffset
    )
    if not 0 < NameSize <= KMaxNameBytes:
        return None
    NameOffset = HeaderOffset + 16
    PayloadOffset = NameOffset + NameSize
    PayloadEnd = PayloadOffset + CompressedSize
    if PayloadOffset > len(BlobValue):
        return None
    NameValue = DecodeName(BlobValue[NameOffset:PayloadOffset], BlobValue[7])
    if NameValue is None:
        return None
    IsCache = (
        UncompressedSize > 0
        and CrcThreeTwoValue == (UncompressedSize * 2) & 4294967295
        and CompressedSize == UncompressedSize // 2
    )
    if UncompressedSize > SizeLimit:
        if IsCache:
            return None
        raise SldprtFormat(f"SLDPRT decoded size limit exceeded by {NameValue!r}")
    if PayloadEnd > len(BlobValue):
        if IsCache:
            return None
        raise SldprtFormat(f"truncated SLDPRT stream {NameValue!r}")
    DataValue = DecodePayload(
        BlobValue[PayloadOffset:PayloadEnd],
        NameValue,
        UncompressedSize,
        CrcThreeTwoValue,
        IsCache,
    )
    if DataValue is None:
        return None
    return StreamRecord(
        name=NameValue,
        data=DataValue,
        offset=Offset,
        payload_offset=PayloadOffset,
        compressed_size=CompressedSize,
        uncompressed_size=UncompressedSize,
        crc32=CrcThreeTwoValue,
        signature=Signature,
    )
