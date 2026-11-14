from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgMapPage:
    PageNumber: int
    PageSize: int
    FileOffset: int
    GapLinks: tuple[int, ...]
