# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.adapters.freecad.EditExtDepth import GetEditDepth
from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from interchange.features.DistanceParam import KLengthFactors
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Expression, Parameter


# original units remain useful unless conversion would round the native depth
def SetEditDepth(Param: Parameter, DistanceMm: float, SourceText: str) -> Parameter:
    UnitValue = Param.value.unit
    Factor = KLengthFactors.get(UnitValue)
    if Factor is None:
        raise ValueError("FreeCAD editable extrusion has unsupported depth units")
    Magnitude = DistanceMm / Factor
    if Magnitude * Factor != DistanceMm:
        Magnitude, UnitValue = DistanceMm, "mm"
    return Replace(
        Param,
        value=Replace(Param.value, value=Magnitude, unit=UnitValue),
        expression=Expression(SourceText, language="freecad"),
    )


# formula edits can update existing values and text without changing native parameter ownership
def MergeDepthEdits(
    Original: tuple[Parameter, ...], ParameterEdits: tuple[Parameter, ...]
) -> tuple[Parameter, ...]:
    ByIdentity = {Value.id: Value for Value in Original}
    EditRows = {Value.id: Value for Value in ParameterEdits}
    if (
        len(ByIdentity) != len(Original)
        or len(EditRows) != len(ParameterEdits)
        or not EditRows.keys() <= ByIdentity.keys()
    ):
        raise ValueError("FreeCAD editable extrusion parameter identities changed")
    for Identity, Edited in EditRows.items():
        Previous = ByIdentity[Identity]
        if (
            Replace(Edited, value=Previous.value, expression=Previous.expression)
            != Previous
        ):
            raise ValueError("FreeCAD editable extrusion parameter ownership changed")
    Result = tuple(EditRows.get(Value.id, Value) for Value in Original)
    return Original if Result == Original else Result


# a profile only edit rebuilds at the exact original depth and keeps its expression
def ReadDepthParams(
    Original: tuple[Parameter, ...],
    Feature: FeatureStep,
    ParameterId: str,
    SourceText: str | None,
    DistanceMm: float,
    ParameterEdits: tuple[Parameter, ...],
) -> tuple[tuple[Parameter, ...], float]:
    Definition = Feature.definition
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.AlongParameterId != ParameterId
    ):
        raise ValueError("FreeCAD editable extrusion depth binding changed")
    if ParameterEdits:
        ParamValues = MergeDepthEdits(Original, ParameterEdits)
    elif SourceText is not None:
        ParamValues = tuple(
            (
                SetEditDepth(Value, DistanceMm, SourceText)
                if Value.id == ParameterId
                else Value
            )
            for Value in Original
        )
    else:
        ParamValues = Original
    DepthMm = GetEditDepth(Feature, Definition, ParamValues)
    if DepthMm is None or not IsClose(
        DepthMm, DistanceMm, rel_tol=0.0, abs_tol=KPositionTolerance
    ):
        raise ValueError(
            "FreeCAD editable extrusion depth disagrees with its parameters"
        )
    return ParamValues, DepthMm
