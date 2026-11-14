from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MatrixValue:
    Entries: tuple[float, ...] | None
