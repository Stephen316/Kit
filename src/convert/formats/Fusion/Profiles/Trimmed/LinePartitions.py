from itertools import combinations as Pairs
from math import isfinite as IsFinite

from convert.formats.Fusion.Profiles.Trimmed.LineTopology import KTrimLine
from convert.formats.Fusion.Profiles.Trimmed.TrimSources import KTrimParameter

# the native squared distance tolerance scales with the sketch length unit conversion
KLineCrossTol = 1e-7


# proper finite line intersections split bounded segments independently of membership order
def FindLineCuts(Sources: dict[str, KTrimLine]) -> dict[str, tuple[float, ...]]:
    CutValues: dict[str, list[float]] = {Identity: [] for Identity in Sources}
    for FirstId, SecondId in Pairs(Sources, 2):
        First, FirstPoints = Sources[FirstId]
        Second, SecondPoints = Sources[SecondId]
        FirstX, FirstY = First.end.x - First.start.x, First.end.y - First.start.y
        SecondX, SecondY = Second.end.x - Second.start.x, Second.end.y - Second.start.y
        OffsetX, OffsetY = (
            Second.start.x - First.start.x,
            Second.start.y - First.start.y,
        )
        Denominator = FirstX * SecondY - FirstY * SecondX
        FirstSide = OffsetX * FirstY - OffsetY * FirstX
        SecondSide = OffsetX * SecondY - OffsetY * SecondX
        if not all(map(IsFinite, (Denominator, FirstSide, SecondSide))):
            raise ValueError("Invalid Fusion trimmed line intersection")
        if abs(Denominator) <= KLineCrossTol:
            if abs(FirstSide) <= KLineCrossTol:
                raise ValueError("Unsupported collinear Fusion trimmed lines")
            continue
        FirstCut, SecondCut = SecondSide / Denominator, FirstSide / Denominator
        if not (
            -KTrimParameter <= FirstCut <= 1.0 + KTrimParameter
            and -KTrimParameter <= SecondCut <= 1.0 + KTrimParameter
        ):
            continue
        FirstInterior = KTrimParameter < FirstCut < 1.0 - KTrimParameter
        SecondInterior = KTrimParameter < SecondCut < 1.0 - KTrimParameter
        if FirstInterior and SecondInterior:
            CutValues[FirstId].append(FirstCut)
            CutValues[SecondId].append(SecondCut)
        elif (
            FirstInterior
            or SecondInterior
            or len(set(FirstPoints) & set(SecondPoints)) != 1
        ):
            raise ValueError(
                "Fusion trimmed line contact is not a shared native corner"
            )
    return FinishLineCuts(CutValues)


# coincident intersections are rejected before their sorted intervals become profile edges
def FinishLineCuts(CutValues: dict[str, list[float]]) -> dict[str, tuple[float, ...]]:
    Result: dict[str, tuple[float, ...]] = {}
    for Identity, Values in CutValues.items():
        Values.sort()
        if any(
            Upper - Lower <= KTrimParameter for Lower, Upper in zip(Values, Values[1:])
        ):
            raise ValueError("Unsupported coincident Fusion trimmed line cuts")
        Result[Identity] = tuple(Values)
    return Result
