# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import GetDistParam, KLengthFactors
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordParameter import Expression, Parameter


# original units remain useful unless conversion would round the native depth
def SetEditDepth(Param: Parameter, DistanceMm: float, SourceText: str) -> Parameter:
    UnitValue = Param.value.unit
    Factor = KLengthFactors[UnitValue]
    Magnitude = DistanceMm / Factor
    if Magnitude * Factor != DistanceMm:
        Magnitude, UnitValue = DistanceMm, "mm"
    return Replace(
        Param,
        value=Replace(Param.value, value=Magnitude, unit=UnitValue),
        expression=Expression(SourceText, language="freecad"),
    )


# rebuilding verified geometry keeps the original identities and body measures consistent
def ApplyDepthEdit(
    DocValue: CadDocument,
    ParameterId: str,
    SourceText: str,
    DistanceMm: float,
    Profile: CircleGeometry,
    FrameValue: Transform,
    ParameterEdits: tuple[Parameter, ...] = (),
) -> CadDocument:
    BodyValue = DocValue.bodies[0]
    if ParameterEdits:
        ByIdentity = {Value.id: Value for Value in DocValue.parameters}
        ByIdentity.update((Value.id, Value) for Value in ParameterEdits)
        ParamValues = tuple(ByIdentity.values())
        DepthMm = GetDistParam(
            DocValue.feature_timeline[-1], ParameterId, ByIdentity, ValueKind.KLength
        )
    else:
        ParamValues = tuple(
            (
                SetEditDepth(Value, DistanceMm, SourceText)
                if Value.id == ParameterId
                else Value
            )
            for Value in DocValue.parameters
        )
        DepthMm = DistanceMm
    Lower, Upper = sorted((0.0, DepthMm))
    BrepValue, Volume, AreaValue, Bounds = BuildCircular(
        BodyValue.id, FrameValue, Profile, Lower, Upper, Profile.radius, Profile.radius
    )
    Topology = Replace(
        BodyValue.topology, volume=Volume, surface_area=AreaValue, bounding_box=Bounds
    )
    return Replace(
        DocValue,
        parameters=ParamValues,
        bodies=(Replace(BodyValue, topology=Topology),),
        brep=BrepValue,
    )
