# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import Sketch


# only a verified profile membership can supply a neutral revolution definition
def ReadRevProfile(
    StepValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry, ...] | CircleGeometry:
    EntityIds = StepValue.attributes.get("fusion.profile_entity_ids")
    if not isinstance(EntityIds, tuple):
        raise ValueError("Missing Fusion Revolve profile selection")
    ByEntity = {Entity.id: Entity.geometry for Entity in SketchValue.entities}
    Parts = tuple(ByEntity.get(Identity) for Identity in EntityIds)
    if len(Parts) == 1 and isinstance(Parts[0], CircleGeometry):
        return Parts[0]
    Lines = tuple(Part for Part in Parts if isinstance(Part, LineGeometry))
    if len(Parts) not in (3, 4) or len(Lines) != len(Parts):
        raise ValueError(
            "Fusion Revolve requires a whole circle or a three or four line profile"
        )
    return Lines
