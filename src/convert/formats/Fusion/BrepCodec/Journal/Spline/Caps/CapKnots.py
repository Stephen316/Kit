from fractions import Fraction
from functools import lru_cache as CacheResult

from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KSectorKnots,
)

# the knot tuple shape must stay shared so spline cap reconstruction uses one contract for compatible values
KKnotTuple = tuple[Fraction, ...]

# degree must remain consistent across callers so extraordinary vertices remain compatible with surrounding patches
KDegree = 3

# clamp must remain consistent across callers so extraordinary vertices remain compatible with surrounding patches
KClamp = 4


# expand knots needs an explicit validity boundary so extraordinary vertices remain compatible with surrounding patches
def ExpandKnots(Knots: KSectorKnots) -> KKnotTuple:
    Values = sorted(Fraction(Value) for Value, Count in Knots for _ in range(Count))
    if not Values:
        raise ValueError("Fusion Form cap rule found a sector without knots")
    Missing = max(0, KClamp - Values.count(Values[0]))
    Expanded = tuple([Values[0]] * Missing + Values)
    StepValue = Expanded[KClamp]
    Wanted = (StepValue, StepValue, 2 * StepValue, 2 * StepValue)
    Found = Expanded[KClamp : KClamp + 4]
    if (
        Values[0] != 0
        or StepValue <= 0
        or Found != Wanted
        or len(Expanded) <= KClamp + 4
    ):
        raise ValueError("Fusion Form cap rule expects double knots at h and 2h")
    return Expanded


# the inside decision must stay consistent so extraordinary vertices remain compatible with surrounding patches
def IsInside(Knots: KKnotTuple, Index: int, Param: Fraction, IsLeft: bool) -> bool:
    Lower, Upper = Knots[Index], Knots[Index + 1]
    if IsLeft:
        return Lower < Param <= Upper
    return Lower <= Param < Upper


# the knot share contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def KnotShare(Value: Fraction, Width: Fraction) -> Fraction:
    return Value / Width if Width else Fraction(0)


# the spline basis contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
@CacheResult(maxsize=None)
def SplineBasis(
    Knots: KKnotTuple, Index: int, Degree: int, Param: Fraction, IsLeft: bool
) -> Fraction:
    if Degree == 0:
        return Fraction(1) if IsInside(Knots, Index, Param, IsLeft) else Fraction(0)
    Lower = KnotShare(Param - Knots[Index], Knots[Index + Degree] - Knots[Index])
    Upper = KnotShare(
        Knots[Index + Degree + 1] - Param, Knots[Index + Degree + 1] - Knots[Index + 1]
    )
    Total = Fraction(0)
    if Lower:
        Total += Lower * SplineBasis(Knots, Index, Degree - 1, Param, IsLeft)
    if Upper:
        Total += Upper * SplineBasis(Knots, Index + 1, Degree - 1, Param, IsLeft)
    return Total


# the basis derive contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
@CacheResult(maxsize=None)
def BasisDerive(
    Knots: KKnotTuple, Param: Fraction, Order: int, IsLeft: bool
) -> tuple[Fraction, ...]:
    Count = len(Knots) - KDegree - 1
    Lowered = KDegree - Order
    Values = [
        SplineBasis(Knots, Index, Lowered, Param, IsLeft)
        for Index in range(Count + Order)
    ]
    for Level in range(Order):
        Degree = Lowered + Level + 1
        Values = [
            Degree
            * (
                KnotShare(Values[Index], Knots[Index + Degree] - Knots[Index])
                - KnotShare(
                    Values[Index + 1], Knots[Index + Degree + 1] - Knots[Index + 1]
                )
            )
            for Index in range(len(Values) - 1)
        ]
    return tuple(Values[:Count])


# knot ratio needs an explicit validity boundary so extraordinary vertices remain compatible with surrounding patches
def KnotRatio(Knots: KKnotTuple) -> Fraction:
    StepValue = Knots[KClamp]
    EdgeValue = 2 * StepValue
    Later = [Value for Value in Knots if Value > EdgeValue]
    if not Later:
        raise ValueError("Fusion Form cap rule found no knot after 2h")
    SpanValue = Later[0] - EdgeValue
    return SpanValue / (StepValue + SpanValue)
