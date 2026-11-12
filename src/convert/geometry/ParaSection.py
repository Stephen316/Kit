from dataclasses import dataclass as DataClass


@DataClass(frozen=True, slots=True)
class ParaSection:
    Data: bytes
    Start: int
    End: int
    CompressedOffset: int
    CompressedSize: int
