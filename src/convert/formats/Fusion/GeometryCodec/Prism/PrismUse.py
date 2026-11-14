from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PrismUse:
    Start: int
    Finish: int
    FaceIndex: int
    RingIndex: int
    EdgeIndex: int
