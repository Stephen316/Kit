from dataclasses import dataclass as Dataclass


# stream record needs an explicit state contract so stream contents retain their geometry and feature relationships
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
