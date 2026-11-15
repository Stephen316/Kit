from dataclasses import dataclass as MakeDataClass


# prism plane needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismPlane:
    OriginCm: tuple[float, float, float]
    Normal: tuple[float, float, float]
    Basis: tuple[float, float, float]
    ReverseV: bool = False
