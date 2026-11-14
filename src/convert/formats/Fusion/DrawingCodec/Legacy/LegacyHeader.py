from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class LegacyHeader:
    Kind: str
    SegmentId: int
    Namespace: str
    Software: int
    Version: int
    RepeatedKind: str
    StorageSpace: str
    StorageWords: tuple[int, int]
