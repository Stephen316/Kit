from dataclasses import dataclass as MakeDataClass


# drawing day time needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgDayTime:
    DayNumber: int
    MilliSeconds: int
