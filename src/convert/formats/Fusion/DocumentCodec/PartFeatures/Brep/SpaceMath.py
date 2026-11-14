from math import sqrt as SquareRoot
from typing import TypeAlias

KSpaceVector: TypeAlias = tuple[float, float, float]
KSpaceTolerance = 1e-7


def AddVector(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (First[0] + Second[0], First[1] + Second[1], First[2] + Second[2])


def SubVector(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (First[0] - Second[0], First[1] - Second[1], First[2] - Second[2])


def ScaleVector(Value: KSpaceVector, Factor: float) -> KSpaceVector:
    return (Value[0] * Factor, Value[1] * Factor, Value[2] * Factor)


def DotProduct(First: KSpaceVector, Second: KSpaceVector) -> float:
    return First[0] * Second[0] + First[1] * Second[1] + First[2] * Second[2]


def CrossProduct(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )


def VectorLength(Value: KSpaceVector) -> float:
    return SquareRoot(DotProduct(Value, Value))


def UnitVector(Value: KSpaceVector) -> KSpaceVector:
    Length = VectorLength(Value)
    if Length < 1e-12:
        raise ValueError("Fusion part geometry needs a nonzero direction")
    return ScaleVector(Value, 1.0 / Length)


def CleanVector(Value: KSpaceVector) -> KSpaceVector:
    return (
        round(Value[0], 12) + 0.0,
        round(Value[1], 12) + 0.0,
        round(Value[2], 12) + 0.0,
    )


def IsSamePoint(First: KSpaceVector, Second: KSpaceVector) -> bool:
    return VectorLength(SubVector(First, Second)) < KSpaceTolerance


def PointAlong(
    Origin: KSpaceVector, Heading: KSpaceVector, Amount: float
) -> KSpaceVector:
    return AddVector(Origin, ScaleVector(Heading, Amount))
