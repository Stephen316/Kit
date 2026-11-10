# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import tan as Tangent
from typing import cast as CastValue

from convert.formats.Fusion.Extrudes.TrimmedParts import ReadTrimParts
from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Extrude.Trimmed.TrimPrism import BuildTrimPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.DistanceValues import DistExtValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# the saved profile and evaluated controls determine an exact bounded swept solid
def BuildExtGeom(
    BodyId: str,
    StepValue: FeatureStep,
    Definition: DistanceExtrude | PlaneExtrude,
    Values: DistExtValues,
    SketchValue: Sketch,
    FrameValue: Transform,
) -> tuple[BrepModel, float, float, BoundingBox]:
    Lower, Upper = Values.LowerMm, Values.UpperMm
    Taper = Values.TaperRadians
    HasTaper = Taper != 0.0 or Values.SecondTaperRadians not in (None, 0.0)
    if "fusion.profile_portions" in StepValue.attributes:
        if HasTaper:
            raise ValueError("Fusion trimmed profile Extrude requires zero draft")
        return BuildTrimPrism(
            BodyId, FrameValue, ReadTrimParts(StepValue, SketchValue), Lower, Upper
        )
    EntityIds = StepValue.attributes.get("fusion.profile_entity_ids")
    if not isinstance(EntityIds, tuple):
        raise ValueError("Missing Fusion Extrude solid profile")
    ByEntity = {Entity.id: Entity.geometry for Entity in SketchValue.entities}
    Parts = tuple(
        ByEntity.get(Identity) for Identity in CastValue(tuple[str, ...], EntityIds)
    )
    if len(Parts) == 1 and isinstance(Parts[0], CircleGeometry):
        Profile = Parts[0]
        if HasTaper and (
            not isinstance(Definition, DistanceExtrude)
            or Definition.SideMode != "one_sided"
            or Definition.StartOffsetId is not None
            or Lower != 0.0
            or Taper <= 0.0
        ):
            raise ValueError("Unsupported Fusion circular Extrude draft controls")
        UpperRadius = Profile.radius + (Upper - Lower) * Tangent(Taper)
        return BuildCircular(
            BodyId, FrameValue, Profile, Lower, Upper, Profile.radius, UpperRadius
        )
    Lines = tuple(
        PartValue for PartValue in Parts if isinstance(PartValue, LineGeometry)
    )
    if len(Lines) >= 3 and len(Lines) == len(Parts) and not HasTaper:
        return BuildPrism(BodyId, FrameValue, Lines, Lower, Upper)
    raise ValueError(
        "Fusion Extrude solid requires a whole circle or an untapered line ring"
    )
