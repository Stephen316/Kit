from typing import cast as CastValue

from convert.Formats.Fusion.Profiles.ArcRing import CheckSemiRing
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
)
from interchange.geometry.Models.Sketch import Sketch


# only a verified profile membership can supply a neutral revolution definition
def ReadRevProfile(
    StepValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry, ...] | CircleGeometry | ArcGeometry:
    EntityIds = StepValue.attributes.get("fusion.profile_entity_ids")
    if not isinstance(EntityIds, tuple):
        raise ValueError("Missing Fusion Revolve profile selection")
    ByEntity = {Entity.id: Entity.geometry for Entity in SketchValue.entities}
    Parts = tuple(
        ByEntity.get(Identity) for Identity in CastValue(tuple[str, ...], EntityIds)
    )
    if len(Parts) == 1 and isinstance(Parts[0], CircleGeometry):
        return Parts[0]
    if (
        len(Parts) == 2
        and isinstance(Parts[0], ArcGeometry)
        and isinstance(Parts[1], LineGeometry)
    ):
        CheckSemiRing(Parts[0], Parts[1])
        return Parts[0]
    Lines = tuple(
        PartValue for PartValue in Parts if isinstance(PartValue, LineGeometry)
    )
    if len(Parts) not in (3, 4) or len(Lines) != len(Parts):
        raise ValueError(
            "Fusion Revolve requires a circle, semicircle with diameter, or three or four lines"
        )
    return Lines
