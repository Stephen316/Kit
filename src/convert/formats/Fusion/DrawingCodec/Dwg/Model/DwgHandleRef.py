from dataclasses import dataclass as MakeDataClass


# drawing handle reference needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgHandleRef:
    RefCode: int
    RefValue: int
