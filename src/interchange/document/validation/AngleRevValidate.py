# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Mapping as TypeMap

from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Selection import Selection
from interchange.records.RecordParameter import Parameter


# angular sweeps can only use parameters owned and linked by the containing feature
def GetLinkedAngle(
    StepValue: FeatureStep,
    ParameterId: str,
    Parameters: TypeMap[str, Parameter],
) -> float:
    Param = Parameters.get(ParameterId)
    if (
        ParameterId not in StepValue.parameter_ids
        or Param is None
        or Param.owner_id != StepValue.id
    ):
        raise ValueError(f"has an unlinked or unowned angle parameter {ParameterId}")
    ValueData = Param.value
    Number = ValueData.value
    if (
        ValueData.kind != ValueKind.KAngle
        or ValueData.unit != "rad"
        or not isinstance(Number, (float, int))
        or isinstance(Number, bool)
    ):
        raise ValueError(f"requires a numeric angle in rad for parameter {ParameterId}")
    return Number


# neutral documents preserve enough reference evidence to recompute angular revolutions
def GetAngleRevErrs(
    StepValue: FeatureStep,
    Definition: AngularRevolve,
    Selections: TypeMap[str, Selection],
    Parameters: TypeMap[str, Parameter],
) -> tuple[str, ...]:
    Errors: list[str] = []
    if StepValue.kind != FeatureKind.KRevolution:
        Errors.append(f"feature {StepValue.id} is not a revolution")
    AxisValue = Selections.get(Definition.AxisSelectionId)
    if Definition.AxisSelectionId not in StepValue.selection_ids:
        Errors.append(
            f"angular revolution {StepValue.id} has an unlinked axis selection"
        )
    if AxisValue is None or not (AxisValue.path or AxisValue.query):
        Errors.append(
            f"angular revolution {StepValue.id} has an unresolved axis selection"
        )
    try:
        Along = GetLinkedAngle(StepValue, Definition.AlongParameterId, Parameters)
        Against = (
            None
            if Definition.AgainstParameterId is None
            else GetLinkedAngle(StepValue, Definition.AgainstParameterId, Parameters)
        )
        _ = GetAngleSpan(Along, Against, Definition.SideMode)
    except ValueError as ErrorInfo:
        Errors.append(
            f"angular revolution {StepValue.id} has invalid angles: {ErrorInfo}"
        )
    return tuple(Errors)
