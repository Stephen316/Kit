# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.geometry.models.VectorPlane import PlaneVector

# binary sketch coordinates share a power of two denominator for exact predicates
KGridPoint = tuple[int, int]


# integer coordinates keep touches and winding unambiguous near the limits of float precision
def ToRingGrid(Points: tuple[PlaneVector, ...]) -> tuple[tuple[KGridPoint, ...], int]:
    Ratios = tuple(
        (PointValue.x.as_integer_ratio(), PointValue.y.as_integer_ratio())
        for PointValue in Points
    )
    Scale = max(Ratio[1] for Coords in Ratios for Ratio in Coords)
    return (
        tuple(
            (XNumerator * (Scale // XDivisor), YNumerator * (Scale // YDivisor))
            for (XNumerator, XDivisor), (YNumerator, YDivisor) in Ratios
        ),
        Scale,
    )


# exact orientation protects both ring winding and segment intersection decisions
def RingTurn(First: KGridPoint, Second: KGridPoint, Third: KGridPoint) -> int:
    return (Second[0] - First[0]) * (Third[1] - First[1]) - (Second[1] - First[1]) * (
        Third[0] - First[0]
    )


# collinear contact must be distinguished from disjoint extensions of the same line
def IsOnSegment(First: KGridPoint, Second: KGridPoint, PointValue: KGridPoint) -> bool:
    return all(
        min(Start, Finish) <= Coordinate <= max(Start, Finish)
        for Start, Finish, Coordinate in zip(First, Second, PointValue)
    )


# closed segment intersections reject crossing and self touching polygon boundaries
def HasCrossing(
    First: KGridPoint, Second: KGridPoint, Third: KGridPoint, Fourth: KGridPoint
) -> bool:
    ThirdTurn = RingTurn(First, Second, Third)
    FourthTurn = RingTurn(First, Second, Fourth)
    FirstTurn = RingTurn(Third, Fourth, First)
    SecondTurn = RingTurn(Third, Fourth, Second)
    return (
        (ThirdTurn * FourthTurn < 0 and FirstTurn * SecondTurn < 0)
        or (ThirdTurn == 0 and IsOnSegment(First, Second, Third))
        or (FourthTurn == 0 and IsOnSegment(First, Second, Fourth))
        or (FirstTurn == 0 and IsOnSegment(Third, Fourth, First))
        or (SecondTurn == 0 and IsOnSegment(Third, Fourth, Second))
    )
