from dataclasses import dataclass as MakeDataClass


# drawing data page needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgDataPage:
    PageNumber: int
    FileOffset: int
    SectionNumber: int
    DataSize: int
    PageSize: int
    StartOffset: int
    HeadChecksum: int
    DataChecksum: int
