from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgPackPlan:
    LeadCount: int
    PackSteps: tuple[tuple[int, int, int], ...]
