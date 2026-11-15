from dataclasses import dataclass as MakeDataClass


# matrix value needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class MatrixValue:
    Entries: tuple[float, ...] | None
