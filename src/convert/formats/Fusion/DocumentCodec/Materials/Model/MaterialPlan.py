from dataclasses import dataclass as MakeDataClass


# material plan needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class MaterialPlan:
    StructuralName: str
    ThermalName: str | None
    FinishName: str
    FinishLocal: str
