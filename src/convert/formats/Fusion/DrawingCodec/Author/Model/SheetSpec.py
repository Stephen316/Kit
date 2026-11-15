from dataclasses import dataclass as MakeDataClass


# sheet specification needs an explicit state contract so sheet objects retain their intended document relationships
@MakeDataClass(frozen=True, slots=True)
class SheetSpec:
    SheetName: str
    SheetSize: str = "A3 Landscape"
    Standard: str = "ISO"
