from math import isfinite as IsFinite
from math import nextafter as NextAfter

from interchange.features.DistanceParam import KLengthFactors


def IsRoundedInch(Displayed: float, NativeValue: float, Decimals: int) -> bool:
    if not IsFinite(NativeValue * KLengthFactors["m"]):
        return False
    NativeInches = NativeValue / (KLengthFactors["in"] / KLengthFactors["m"])
    HalfStep = 0.5 * 10**-Decimals
    return (
        NextAfter(Displayed - HalfStep, -float("inf"))
        <= NativeInches
        <= NextAfter(Displayed + HalfStep, float("inf"))
    )
