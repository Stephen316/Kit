from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SheetLayout:
    ActiveSheet: str
    SheetSize: str
    Standard: str
    Units: str
    Width: float
    Height: float
    HorizontalZones: int
    VerticalZones: int
