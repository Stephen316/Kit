from dataclasses import dataclass as MakeDataClass
from math import pi as CirclePi
from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.DistanceSpan import GetDistSpan
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# geometry builders need evaluated dimensions without replacing the editable definition
@MakeDataClass(frozen=True, slots=True)
class DistExtValues:
    LowerMm: float
    UpperMm: float
    OffsetMm: float
    TaperRadians: float
    SecondTaperRadians: float | None


# source readers and geometry builders share one checked evaluation of owned controls
def GetDistValues(
    StepValue: FeatureStep,
    Definition: DistanceExtrude,
    Parameters: TypeMap[str, Parameter],
) -> DistExtValues:
    if (
        StepValue.kind != FeatureKind.KExtrusion
        or StepValue.operation != BooleanOp.KCreate
    ):
        raise ValueError("distance extrusion requires a create extrusion feature")
    Along = GetDistParam(
        StepValue, Definition.AlongParameterId, Parameters, ValueKind.KLength
    )
    Against, Offset, Taper, SecondTaper = (
        (
            None
            if Identity is None
            else GetDistParam(StepValue, Identity, Parameters, KindValue)
        )
        for Identity, KindValue in (
            (Definition.AgainstParameterId, ValueKind.KLength),
            (Definition.StartOffsetId, ValueKind.KLength),
            (Definition.TaperParameterId, ValueKind.KAngle),
            (Definition.SecondTaperId, ValueKind.KAngle),
        )
    )
    if any(
        Value is not None and abs(Value) >= CirclePi / 2.0
        for Value in (Taper, SecondTaper)
    ):
        raise ValueError("distance extrusion taper must be less than a right angle")
    OffsetMm = 0.0 if Offset is None else Offset
    LowerMm, UpperMm = GetDistSpan(Along, Against, OffsetMm, Definition.SideMode)
    return DistExtValues(
        LowerMm, UpperMm, OffsetMm, 0.0 if Taper is None else Taper, SecondTaper
    )
