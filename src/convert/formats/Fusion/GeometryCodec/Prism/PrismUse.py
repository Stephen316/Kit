from dataclasses import dataclass as MakeDataClass


# prism use needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class PrismUse:
    Start: int
    Finish: int
    FaceIndex: int
    RingIndex: int
    EdgeIndex: int
