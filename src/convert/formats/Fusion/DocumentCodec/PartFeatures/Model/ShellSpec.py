from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ShellSpec:
    ThicknessMm: float
    FeatureName: str = "Shell"
    SidesMm: tuple[tuple[float, float], ...] = ()
