from math import sqrt as SquareRoot
from typing import TypeAlias

# the space vector shape must stay shared so feature geometry uses one contract for compatible values
KSpaceVector: TypeAlias = tuple[float, float, float]

# the space tolerance tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KSpaceTolerance = 1e-7


# the vector operation needs a consistent construction rule so edge and face relationships survive parametric feature construction
def AddVector(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (First[0] + Second[0], First[1] + Second[1], First[2] + Second[2])


# the sub vector contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def SubVector(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (First[0] - Second[0], First[1] - Second[1], First[2] - Second[2])


# the vector operation needs one geometric convention so edge and face relationships survive parametric feature construction
def ScaleVector(Value: KSpaceVector, Factor: float) -> KSpaceVector:
    return (Value[0] * Factor, Value[1] * Factor, Value[2] * Factor)


# the product operation needs one geometric convention so edge and face relationships survive parametric feature construction
def DotProduct(First: KSpaceVector, Second: KSpaceVector) -> float:
    return First[0] * Second[0] + First[1] * Second[1] + First[2] * Second[2]


# the product operation needs one geometric convention so edge and face relationships survive parametric feature construction
def CrossProduct(First: KSpaceVector, Second: KSpaceVector) -> KSpaceVector:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )


# the length operation needs one geometric convention so edge and face relationships survive parametric feature construction
def VectorLength(Value: KSpaceVector) -> float:
    return SquareRoot(DotProduct(Value, Value))


# the vector operation needs one geometric convention so edge and face relationships survive parametric feature construction
def UnitVector(Value: KSpaceVector) -> KSpaceVector:
    Length = VectorLength(Value)
    if Length < 1e-12:
        raise ValueError("Fusion part geometry needs a nonzero direction")
    return ScaleVector(Value, 1.0 / Length)


# the clean vector contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def CleanVector(Value: KSpaceVector) -> KSpaceVector:
    return (
        round(Value[0], 12) + 0.0,
        round(Value[1], 12) + 0.0,
        round(Value[2], 12) + 0.0,
    )


# the same point decision must stay consistent so edge and face relationships survive parametric feature construction
def IsSamePoint(First: KSpaceVector, Second: KSpaceVector) -> bool:
    return VectorLength(SubVector(First, Second)) < KSpaceTolerance


# the along operation needs one geometric convention so edge and face relationships survive parametric feature construction
def PointAlong(
    Origin: KSpaceVector, Heading: KSpaceVector, Amount: float
) -> KSpaceVector:
    return AddVector(Origin, ScaleVector(Heading, Amount))
