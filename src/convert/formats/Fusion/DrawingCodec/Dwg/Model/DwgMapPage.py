from dataclasses import dataclass as MakeDataClass


# drawing map page needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgMapPage:
    PageNumber: int
    PageSize: int
    FileOffset: int
    GapLinks: tuple[int, ...]
