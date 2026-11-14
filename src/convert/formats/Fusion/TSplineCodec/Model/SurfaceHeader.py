from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceHeader:
    Degree: int = 3
    CapType: str = "G1CAPS"
    StarSmoothness: float = 0.0
    UnitScale: float = 1.0
    UnitName: str = "meters"
    EndConditions: str = "SUBD_CREASES"
    StarKnotRule: str = "NURCCS"
    Tolerance: float = 1e-5
    GeometryTol: float = 1e-5
    VersionCount: int = 0
    BehaviorVersion: str = "14.2.0"
    CompatVersion: str = "13.3.0"
