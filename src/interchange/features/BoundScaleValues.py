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

from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter, ParameterValue


# a scale value must be dimensionless and owned by the feature that uses it
def ReadScaleFactor(
    StepValue: FeatureStep, Identity: str, Parameters: TypeMap[str, Parameter]
) -> float:
    Param = Parameters.get(Identity)
    if (
        Param is None
        or Param.owner_id != StepValue.id
        or Identity not in StepValue.parameter_ids
    ):
        raise ValueError("scale factor parameter is missing or unowned")
    DataValue = Param.value
    if (
        not isinstance(DataValue, ParameterValue)
        or DataValue.kind != ValueKind.KNumber
        or DataValue.unit
        or type(DataValue.value) not in (float, int)
        or not 0 < DataValue.value <= FloatInfo.max
    ):
        raise ValueError("scale factors must be finite positive dimensionless numbers")
    return float(DataValue.value)


# geometry and validation resolve the same ordered scale parameters and center
def GetScaleValues(
    StepValue: FeatureStep,
    Definition: BoundScale,
    Params: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[SpaceVector, SpaceVector]:
    if StepValue.kind != FeatureKind.KScale:
        raise ValueError("bound scale requires a scale feature")
    Center = Selections.get(Definition.CenterSelectionId)
    if (
        Center is None
        or Center.point is None
        or not all(
            IsFinite(Value)
            for Value in (Center.point.x, Center.point.y, Center.point.z)
        )
    ):
        raise ValueError("scale requires a finite selected center")
    for Identity in (Definition.CenterSelectionId, *Definition.BodySelectionIds):
        if Identity not in StepValue.selection_ids or Identity not in Selections:
            raise ValueError("scale has an unlinked selection")
    Factors = tuple(
        ReadScaleFactor(StepValue, Identity, Params)
        for Identity in Definition.FactorParameterIds
    )
    return SpaceVector(*(Factors * 3 if len(Factors) == 1 else Factors)), Center.point
