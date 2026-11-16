from dataclasses import dataclass as MakeDataClass


# boundary use needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class BoundaryUse:
    CoedgeRef: int
    EdgeRef: int
    StartVertex: int
    EndVertex: int
    PartnerRef: int
