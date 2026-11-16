from dataclasses import dataclass as MakeDataClass


# entry layout needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class EntryLayout:
    Method: int
    Flags: int
    Time: int
    Date: int
    Creator: int
    Extract: int
    Attributes: int
