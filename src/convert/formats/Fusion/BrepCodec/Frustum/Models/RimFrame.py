from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RimFrame:
    CenterCm: tuple[float, float, float]
    Normal: tuple[float, float, float]
    MajorVectorCm: tuple[float, float, float]
    Ratio: float
    PointCm: tuple[float, float, float]
    PlaneOriginCm: tuple[float, float, float]
    PlaneNormal: tuple[float, float, float]
    PlaneBasis: tuple[float, float, float]
    PlaneReverseV: bool
    EdgeStart: float
    EdgeEnd: float
    EdgeReverse: bool
    SideReverse: bool
    CapReverse: bool
    VertexIndex: int
