from dataclasses import dataclass as MakeDataClass


# shell specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class ShellSpec:
    ThicknessMm: float
    FeatureName: str = "Shell"
    SidesMm: tuple[tuple[float, float], ...] = ()
