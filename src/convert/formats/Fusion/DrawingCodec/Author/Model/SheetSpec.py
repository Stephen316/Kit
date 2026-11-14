from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SheetSpec:
    SheetName: str
    SheetSize: str = "A3 Landscape"
    Standard: str = "ISO"
