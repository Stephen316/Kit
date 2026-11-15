from dataclasses import dataclass as MakeDataClass


# stencil curve needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class StencilCurve:
    Knots: tuple[float, ...]
    Multiplicity: tuple[int, ...]
    Poles: tuple[int, ...]
