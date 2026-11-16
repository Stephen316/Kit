from math import isclose as IsClose

from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import KAsmMatchTol
from convert.Formats.Fusion.Topology.CutResult.CutMetricBox import (
    AxisValues,
    CutMetricBox,
)
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature


# the cavity must start at the saved inward cut direction and agree with the typed extent
def CheckCutPocket(
    Outer: CutMetricBox, Inner: CutMetricBox, Definition: ExtrudeFeature
) -> tuple[int, frozenset[bool]]:
    Direction = Definition.direction
    if Direction is None:
        raise ValueError("Fusion Cut mass lacks the verified cutting direction")
    Coords = AxisValues(Direction)
    Active = tuple(Index for Index, Value in enumerate(Coords) if abs(Value) > 1e-9)
    if len(Active) != 1 or not IsClose(
        abs(Coords[Active[0]]), 1.0, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError("Fusion Cut mass requires an axis aligned direction")
    (AxisIndex,) = Active
    HighStart = Coords[AxisIndex] < 0
    if any(
        Inner.Lower[Index] <= Outer.Lower[Index] + KAsmMatchTol
        or Inner.Upper[Index] >= Outer.Upper[Index] - KAsmMatchTol
        for Index in range(3)
        if Index != AxisIndex
    ):
        raise ValueError("Fusion Cut cavity leaves the outer box sides")
    OuterLimits = Outer.Lower[AxisIndex], Outer.Upper[AxisIndex]
    InnerLimits = Inner.Lower[AxisIndex], Inner.Upper[AxisIndex]
    Openings = frozenset(
        bool(Index)
        for Index in range(2)
        if IsClose(
            OuterLimits[Index], InnerLimits[Index], rel_tol=0.0, abs_tol=KAsmMatchTol
        )
    )
    if (
        HighStart not in Openings
        or InnerLimits[0] < OuterLimits[0] - KAsmMatchTol
        or InnerLimits[1] > OuterLimits[1] + KAsmMatchTol
    ):
        raise ValueError("Fusion Cut cavity leaves the saved start or axial bounds")
    if Definition.end_condition == ExtrudeEnd.KThroughAll:
        if len(Openings) != 2 or Definition.length is not None:
            raise ValueError("Fusion through all cavity requires two openings")
        return AxisIndex, Openings
    Length = Definition.length
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or len(Openings) != 1
        or Length is None
        or Length.kind != ValueKind.KLength
        or Length.unit != "cm"
        or type(Length.value) not in (float, int)
        or not IsClose(
            InnerLimits[1] - InnerLimits[0],
            float(Length.value) * 10.0,
            rel_tol=0.0,
            abs_tol=KAsmMatchTol,
        )
    ):
        raise ValueError("Fusion blind cavity and authored depth disagree")
    return AxisIndex, Openings
