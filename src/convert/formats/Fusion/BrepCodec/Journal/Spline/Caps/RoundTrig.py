from decimal import Context, Decimal, localcontext
from functools import cache as CacheValue
from math import isfinite as IsFinite

KPrecision = 90

KAngleLimit = 1.0e6

KContext = Context(prec=KPrecision)


def ArcInverse(Divisor: int) -> Decimal:
    Power = Decimal(1) / Divisor
    Total = Power
    Square = Divisor * Divisor
    Bound = Decimal(10) ** -KPrecision
    Index = 1
    while Power > Bound:
        Power /= Square
        Piece = Power / (2 * Index + 1)
        Total = Total - Piece if Index % 2 else Total + Piece
        Index += 1
    return Total


@CacheValue
def FullPeriod() -> Decimal:
    with localcontext(KContext):
        return 2 * (16 * ArcInverse(5) - 4 * ArcInverse(239))


@CacheValue
def RoundTrig(Angle: float) -> tuple[float, float]:
    if not IsFinite(Angle) or abs(Angle) > KAngleLimit:
        raise ValueError("Angle is outside the exact trigonometry range")
    Period = FullPeriod()
    with localcontext(KContext):
        Exact = Decimal(Angle)
        Reduced = Exact - Period * (Exact / Period).to_integral_value()
        Square = Reduced * Reduced
        CosTerm, SinTerm = Decimal(1), Reduced
        CosTotal, SinTotal = CosTerm, SinTerm
        Bound = Decimal(10) ** -(KPrecision - 6)
        Index = 1
        while abs(CosTerm) > Bound or abs(SinTerm) > Bound:
            CosTerm = -CosTerm * Square / ((2 * Index - 1) * (2 * Index))
            SinTerm = -SinTerm * Square / ((2 * Index) * (2 * Index + 1))
            CosTotal += CosTerm
            SinTotal += SinTerm
            Index += 1
        return float(CosTotal), float(SinTotal)


def RoundCosine(Angle: float) -> float:
    return RoundTrig(Angle)[0]


def RoundSine(Angle: float) -> float:
    return RoundTrig(Angle)[1]
