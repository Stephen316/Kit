from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MetaIndex import SegmentKind


# typed segment headers retain uninterpreted words alongside the known version fields
@MakeDataClass(frozen=True, slots=True)
class MetaHeader:
    Segment: SegmentKind
    SegmentId: int
    Namespace: str
    Magic: int
    Version: int
    HeaderWords: tuple[int, int]
    RepeatedKind: str
    StorageSpace: str
    StorageWords: tuple[int, int]
