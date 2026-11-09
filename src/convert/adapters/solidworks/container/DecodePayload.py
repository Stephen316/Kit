# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from zlib import crc32 as Checksum
from convert.adapters.solidworks.container.InflateStream import InflateStream
from convert.adapters.solidworks.container.SldprtFormat import SldprtFormat


def DecodePayload(
    Payload: bytes,
    NameValue: str,
    ExpectedSize: int,
    ChecksumValue: int,
    IsCache: bool,
) -> bytes | None:
    DataValue = InflateStream(Payload, ExpectedSize)
    if DataValue is None:
        if IsCache:
            return None
        raise SldprtFormat(f"invalid compressed SLDPRT stream {NameValue!r}")
    if Checksum(DataValue) & 4294967295 != ChecksumValue:
        if IsCache:
            return None
        raise SldprtFormat(f"SLDPRT checksum mismatch for {NameValue!r}")
    return DataValue
