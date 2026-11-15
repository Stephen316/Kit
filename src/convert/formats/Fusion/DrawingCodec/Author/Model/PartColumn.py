from dataclasses import dataclass as MakeDataClass


# part column needs an explicit state contract so sheet objects retain their intended document relationships
@MakeDataClass(frozen=True, slots=True)
class PartColumn:
    Ident: str
    DisplayName: str
    Visible: bool
    WidthIso: int | float
    WidthAsme: int | float
    Shown: bool
    Group: str = ""
