from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgDayTime:
    DayNumber: int
    MilliSeconds: int
