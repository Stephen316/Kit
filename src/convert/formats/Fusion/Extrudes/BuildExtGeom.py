# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import tan as Tangent

from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.DistanceValues import DistExtValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# the saved profile and evaluated controls determine an exact bounded swept solid
def BuildExtGeom(
    BodyId: str,
    StepValue: FeatureStep,
    Definition: DistanceExtrude,
    Values: DistExtValues,
    SketchValue: Sketch,
    FrameValue: Transform,
) -> tuple[BrepModel, float, float, BoundingBox]:
    EntityIds = StepValue.attributes.get("fusion.profile_entity_ids")
    if not isinstance(EntityIds, tuple):
        raise ValueError("Missing Fusion Extrude solid profile")
    ByEntity = {Entity.id: Entity.geometry for Entity in SketchValue.entities}
    Parts = tuple(ByEntity.get(Identity) for Identity in EntityIds)
    Lower, Upper = Values.LowerMm, Values.UpperMm
    Taper = Values.TaperRadians
    HasTaper = Taper != 0.0 or Values.SecondTaperRadians not in (None, 0.0)
    if len(Parts) == 1 and isinstance(Parts[0], CircleGeometry):
        Profile = Parts[0]
        if HasTaper and (
            Definition.SideMode != "one_sided"
            or Definition.StartOffsetId is not None
            or Lower != 0.0
            or Taper <= 0.0
        ):
            raise ValueError("Unsupported Fusion circular Extrude draft controls")
        UpperRadius = Profile.radius + (Upper - Lower) * Tangent(Taper)
        return BuildCircular(
            BodyId, FrameValue, Profile, Lower, Upper, Profile.radius, UpperRadius
        )
    Lines = tuple(Part for Part in Parts if isinstance(Part, LineGeometry))
    if len(Lines) >= 3 and len(Lines) == len(Parts) and not HasTaper:
        return BuildPrism(BodyId, FrameValue, Lines, Lower, Upper)
    raise ValueError(
        "Fusion Extrude solid requires a whole circle or an untapered line ring"
    )
