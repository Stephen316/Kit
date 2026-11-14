from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ColorValue:
    RedValue: float
    GreenValue: float
    BlueValue: float
    AlphaValue: float
