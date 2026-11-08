# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from math import pi as Pi
from typing import Mapping as TypeMap

from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import GetDistParam
from interchange.features.DistanceSpan import GetDistSpan
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


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
            else GetDistParam(StepValue, Identity, Parameters, Kind)
        )
        for Identity, Kind in (
            (Definition.AgainstParameterId, ValueKind.KLength),
            (Definition.StartOffsetId, ValueKind.KLength),
            (Definition.TaperParameterId, ValueKind.KAngle),
            (Definition.SecondTaperId, ValueKind.KAngle),
        )
    )
    if any(
        Value is not None and abs(Value) >= Pi / 2.0 for Value in (Taper, SecondTaper)
    ):
        raise ValueError("distance extrusion taper must be less than a right angle")
    OffsetMm = 0.0 if Offset is None else Offset
    LowerMm, UpperMm = GetDistSpan(Along, Against, OffsetMm, Definition.SideMode)
    return DistExtValues(
        LowerMm, UpperMm, OffsetMm, 0.0 if Taper is None else Taper, SecondTaper
    )
