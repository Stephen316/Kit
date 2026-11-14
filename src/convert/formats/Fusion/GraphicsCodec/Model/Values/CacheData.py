from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CacheData:
    ModeValue: int
    AxisValue: tuple[float, ...]
    Bounds: tuple[float, ...]
    BakedMatrix: tuple[float, ...]
    MappingMatrix: tuple[float, ...]
    CylinderCap: bool | None = None
    SquareCap: bool | None = None
    WoodOrigin: tuple[float, ...] | None = None
    WoodAxis: tuple[float, ...] | None = None
