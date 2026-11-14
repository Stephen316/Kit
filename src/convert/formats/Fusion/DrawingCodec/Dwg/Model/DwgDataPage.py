from dataclasses import dataclass as MakeDataClass


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
