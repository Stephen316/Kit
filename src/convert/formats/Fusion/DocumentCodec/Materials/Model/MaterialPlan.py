from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MaterialPlan:
    StructuralName: str
    ThermalName: str | None
    FinishName: str
    FinishLocal: str
