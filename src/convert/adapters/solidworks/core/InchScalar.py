from math import isfinite as IsFinite
from re import fullmatch as FullMatch

from interchange.features.DistanceParam import KLengthFactors


def IsRoundedInch(TextValue: str, NativeValue: float, Decimals: int) -> bool:
    LengthMm = NativeValue * KLengthFactors["m"]
    if not IsFinite(LengthMm) or LengthMm <= 0.0:
        return False
    TextValue = TextValue.strip()
    if FullMatch(r"[0-9]+(?:\.[0-9]+)?", TextValue) is None:
        return False
    Rounded = round(LengthMm / KLengthFactors["in"], Decimals)
    return Rounded == float(TextValue)
