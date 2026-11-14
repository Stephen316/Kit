from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class IndexData:
    DynamicFlag: bool
    StreamIndex: int
    ByteOffset: int
    IsShort: bool
    Values: tuple[int, ...]
