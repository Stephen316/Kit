from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class StencilCurve:
    Knots: tuple[float, ...]
    Multiplicity: tuple[int, ...]
    Poles: tuple[int, ...]
