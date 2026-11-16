from dataclasses import dataclass as MakeDataClass


# legacy header needs an explicit state contract so drawing members retain their sheet and model associations
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
