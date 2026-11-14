from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BoundaryUse:
    CoedgeRef: int
    EdgeRef: int
    StartVertex: int
    EndVertex: int
    PartnerRef: int
