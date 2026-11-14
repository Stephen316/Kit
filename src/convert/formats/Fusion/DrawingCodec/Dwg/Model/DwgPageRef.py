from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgPageRef:
    PageNumber: int
    DataSize: int
    StartOffset: int
