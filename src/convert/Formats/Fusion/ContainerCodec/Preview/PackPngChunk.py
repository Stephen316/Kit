from struct import pack as PackValue
from zlib import crc32 as CrcValue


# the pack png chunk contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def PackPngChunk(KindValue: bytes, Payload: bytes) -> bytes:
    Checksum = CrcValue(Payload, CrcValue(KindValue))
    return (
        PackValue(">I", len(Payload)) + KindValue + Payload + PackValue(">I", Checksum)
    )
