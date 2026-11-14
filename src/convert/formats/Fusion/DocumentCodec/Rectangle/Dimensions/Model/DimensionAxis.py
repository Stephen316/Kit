from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DimensionAxis:
    RoleName: str
    ParamName: str
    LengthMm: float
    PointRoles: tuple[str, str]
    StartPoint: tuple[float, float, float]
    EndPoint: tuple[float, float, float]
    Offset: tuple[float, float, float]
    ConstraintType: int
