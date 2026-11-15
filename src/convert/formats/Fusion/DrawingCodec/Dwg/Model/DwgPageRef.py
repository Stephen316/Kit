from dataclasses import dataclass as MakeDataClass


# drawing page reference needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgPageRef:
    PageNumber: int
    DataSize: int
    StartOffset: int
