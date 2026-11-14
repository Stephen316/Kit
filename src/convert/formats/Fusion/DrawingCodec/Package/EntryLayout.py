from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EntryLayout:
    Method: int
    Flags: int
    Time: int
    Date: int
    Creator: int
    Extract: int
    Attributes: int
