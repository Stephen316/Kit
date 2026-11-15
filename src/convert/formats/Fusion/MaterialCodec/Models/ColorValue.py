from dataclasses import dataclass as MakeDataClass


# color value needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class ColorValue:
    RedValue: float
    GreenValue: float
    BlueValue: float
    AlphaValue: float
