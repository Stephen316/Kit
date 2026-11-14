from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgHandleMap:
    HandleCount: int
    LastHandle: int
    BlockCount: int
