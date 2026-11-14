from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class TitleText:
    Tag: str
    TextValue: str
    WidthFactor: float = 1.0
