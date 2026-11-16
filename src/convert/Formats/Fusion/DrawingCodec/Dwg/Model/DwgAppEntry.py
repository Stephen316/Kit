from dataclasses import dataclass as MakeDataClass


# drawing app entry needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgAppEntry:
    KeyBytes: bytes
    TextValue: str
