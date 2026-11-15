from dataclasses import dataclass as MakeDataClass


# index data needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class IndexData:
    DynamicFlag: bool
    StreamIndex: int
    ByteOffset: int
    IsShort: bool
    Values: tuple[int, ...]
