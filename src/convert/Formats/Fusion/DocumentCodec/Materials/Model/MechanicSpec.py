from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)


# mechanic specification needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class MechanicSpec:
    YoungModulus: float | None = None
    PoissonRatio: float | None = None
    ShearModulus: float | None = None
    YieldStrength: float | None = None
    TensileStrength: float | None = None
    Conductivity: float | None = None
    SpecificHeat: float | None = None
    Expansion: float | None = None
    Damping: float | None = None
    AverageModulus: float | None = None
    Bending: float | None = None
    CompressAlong: float | None = None
    CompressAcross: float | None = None
    ShearAlong: float | None = None
    TensionAlong: float | None = None
    TensionAcross: float | None = None
    Behavior: str | None = None
    Directional: tuple[DirectionValue, ...] = ()
