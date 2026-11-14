from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PartColumn:
    Ident: str
    DisplayName: str
    Visible: bool
    WidthIso: int | float
    WidthAsme: int | float
    Shown: bool
    Group: str = ""
