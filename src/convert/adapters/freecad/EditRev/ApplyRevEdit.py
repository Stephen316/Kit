# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRing.RingChange import CheckRingEdit
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordParameter import Expression, Parameter


# keep original native ownership and literal spelling when a saved angle is unchanged
def SetRevAngle(Param: Parameter, Radians: float, SourceText: str) -> Parameter:
    if Param.value.value == Radians:
        return Param
    return Replace(
        Param,
        value=Replace(Param.value, value=Radians),
        expression=Expression(SourceText, language="freecad"),
    )


# one neutral rebuild keeps the edited controls and the original solid identity together
def ApplyRevEdit(
    DocValue: CadDocument,
    Profile: Sketch,
    Along: tuple[float, str],
    Against: tuple[float, str] | None,
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if not isinstance(Definition, AngularRevolve):
        raise ValueError("FreeCAD editable Revolve source definition is unavailable")
    if (Definition.AgainstParameterId is None) != (Against is None):
        raise ValueError("FreeCAD editable Revolve against angle binding changed")
    AngleEdits = {Definition.AlongParameterId: Along}
    if Definition.AgainstParameterId is not None and Against is not None:
        AngleEdits[Definition.AgainstParameterId] = Against
    Parameters = tuple(
        SetRevAngle(Value, *AngleEdits[Value.id]) for Value in DocValue.parameters
    )
    (Original,) = DocValue.sketches
    if Profile == Original and Parameters == DocValue.parameters:
        return DocValue
    if Profile != Original:
        CheckRingEdit(Original, Profile)
    AlongValue, AgainstValue = ReadRevAngles(Feature, Definition, Parameters)
    Span = GetAngleSpan(AlongValue, AgainstValue, Definition.SideMode)
    (BodyValue,) = DocValue.bodies
    (PlaneValue,) = DocValue.support_planes
    Model, Volume, AreaValue, Bounds = BuildRevGeom(
        BodyValue.id, Feature, Definition, Span, Profile, PlaneValue.transform
    )
    Topology = Replace(
        BodyValue.topology,
        solid_count=len(Model.regions),
        shell_count=len(Model.shells),
        face_count=len(Model.faces),
        edge_count=len(Model.edges),
        vertex_count=len(Model.vertices),
        volume=Volume,
        surface_area=AreaValue,
        bounding_box=Bounds,
        valid=True,
    )
    if len(Model.regions) != 1 or Model.validate(frozenset({BodyValue.id})):
        raise ValueError("FreeCAD editable Revolve rebuilt an invalid solid")
    return Replace(
        DocValue,
        parameters=Parameters,
        sketches=(Profile,),
        bodies=(Replace(BodyValue, topology=Topology),),
        brep=Model,
    )
