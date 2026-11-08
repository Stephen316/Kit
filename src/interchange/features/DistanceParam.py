# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from sys import float_info as FloatInfo
from typing import Mapping as TypeMap

from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter, ParameterValue

# accepted length units resolve to the neutral geometry unit without modifying the binding
KLengthFactors = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}


# geometry consumers must read each dimensional value through the exact owned binding
def GetDistParam(
    StepValue: FeatureStep,
    Identity: str,
    Parameters: TypeMap[str, Parameter],
    Kind: ValueKind,
) -> float:
    Param = Parameters.get(Identity)
    if (
        Param is None
        or Param.owner_id != StepValue.id
        or Identity not in StepValue.parameter_ids
    ):
        raise ValueError(f"unlinked or unowned extrusion parameter {Identity}")
    ValueData = Param.value
    if not isinstance(ValueData, ParameterValue):
        raise ValueError(f"extrusion parameter {Identity} has no typed value")
    Number = ValueData.value
    if (
        ValueData.kind != Kind
        or not isinstance(Number, (float, int))
        or isinstance(Number, bool)
        or not -FloatInfo.max <= Number <= FloatInfo.max
    ):
        raise ValueError(
            f"extrusion parameter {Identity} requires a finite numeric {Kind.value}"
        )
    UnitName = ValueData.unit
    if Kind == ValueKind.KLength and isinstance(UnitName, str):
        Factor = KLengthFactors.get(UnitName)
    else:
        Factor = 1.0 if Kind == ValueKind.KAngle and UnitName == "rad" else None
    if Factor is None or not IsFinite(Number * Factor):
        raise ValueError(
            f"extrusion parameter {Identity} has unsupported units or magnitude"
        )
    return Number * Factor
