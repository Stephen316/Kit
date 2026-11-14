from struct import pack as PackValue
from zlib import crc32 as CrcValue


def PackPngChunk(KindValue: bytes, Payload: bytes) -> bytes:
    Checksum = CrcValue(Payload, CrcValue(KindValue))
    return (
        PackValue(">I", len(Payload)) + KindValue + Payload + PackValue(">I", Checksum)
    )
