from dataclasses import dataclass as MakeDataClass


# material ids needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class MaterialIds:
    PackageId: str
    AssetId: str
    LibraryId: str
    PhysicalId: str
    StructuralId: str
    ThermalId: str
    AppearanceId: str
    PhysicalDef: str
    StructuralDef: str
    ThermalDef: str
    AppearanceDef: str
    PartName: str
