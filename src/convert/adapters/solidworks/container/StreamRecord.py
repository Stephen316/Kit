from dataclasses import dataclass as Dataclass


@Dataclass(frozen=True, slots=True)
class StreamRecord:
    name: str
    data: bytes
    offset: int
    payload_offset: int
    compressed_size: int
    uncompressed_size: int
    crc32: int
    signature: bytes
