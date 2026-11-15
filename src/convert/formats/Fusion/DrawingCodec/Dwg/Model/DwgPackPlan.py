from dataclasses import dataclass as MakeDataClass


# drawing pack plan needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgPackPlan:
    LeadCount: int
    PackSteps: tuple[tuple[int, int, int], ...]
