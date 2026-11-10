# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.formats.Fusion.Topology.AsmEdge.PrismProfile import ReadProfileTags
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# a selected source retains its original lines and named cache correspondence
@MakeDataClass(frozen=True, slots=True)
class ScaleSeed:
    Profile: tuple[LineGeometry, ...]
    Frame: Transform
    Depth: float
    CurveTags: tuple[int, ...]


# only an independently editable untapered prism can supply this scale reconstruction
def ReadScaleSeed(
    Document: CadDocument, Source: FeatureStep, ComponentId: int
) -> ScaleSeed:
    Definition = Source.definition
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.SideMode != "one_sided"
        or Definition.StartOffsetId is not None
        or Definition.Direction != SpaceVector(0, 0, 1)
        or "fusion.profile_portions" in Source.attributes
    ):
        raise ValueError("Fusion Scale needs a plain signed prism source Extrude")
    Values = GetDistValues(
        Source, Definition, {Value.id: Value for Value in Document.parameters}
    )
    if (
        Values.OffsetMm != 0
        or Values.TaperRadians != 0
        or Values.SecondTaperRadians not in (None, 0)
    ):
        raise ValueError("Fusion Scale source prism has taper or an offset")
    SketchValue = next(
        (Value for Value in Document.sketches if Value.id == Source.sketch_id), None
    )
    if SketchValue is None:
        raise ValueError("Fusion Scale source sketch is missing")
    Frame = next(
        (
            Value
            for Value in Document.support_planes
            if Value.id == SketchValue.support_plane_id
        ),
        None,
    )
    if (
        Frame is None
        or Frame.attributes.get("fusion.component_object_id") != ComponentId
    ):
        raise ValueError("Fusion Scale source sketch component disagrees")
    Identities = Source.attributes.get("fusion.profile_entity_ids")
    if not IsObjectTuple(Identities):
        raise ValueError("Fusion Scale source profile is missing")
    ByIdentity = {Value.id: Value for Value in SketchValue.entities}
    if any(
        not isinstance(Identity, str) or Identity not in ByIdentity
        for Identity in Identities
    ):
        raise ValueError("Fusion Scale source profile has an unresolved entity")
    Profile = tuple(
        ByIdentity[Identity] for Identity in CastValue(tuple[str, ...], Identities)
    )
    TagValues = ReadProfileTags(Profile)
    Lines = tuple(
        Entity.geometry
        for Entity in Profile
        if isinstance(Entity.geometry, LineGeometry)
    )
    Depth = Values.LowerMm if Values.LowerMm < 0.0 else Values.UpperMm
    return ScaleSeed(Lines, Frame.transform, Depth, TagValues)
