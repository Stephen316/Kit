# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch


# whole sketch links can reproduce a selected circle when the remaining entities are helper points
def GetEditCircle(
    FeatureValue: FeatureStep, SketchValue: Sketch
) -> CircleGeometry | None:
    Membership = FeatureValue.attributes.get("fusion.profile_entity_ids")
    DescriptorId = FeatureValue.attributes.get("fusion.profile_descriptor_id")
    if (
        FeatureValue.sketch_id != SketchValue.id
        or SketchValue.suppressed
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or type(DescriptorId) is not int
        or DescriptorId <= 0
        or "fusion.profile_portions" in FeatureValue.attributes
        or not isinstance(Membership, tuple)
        or len(Membership) != 1
        or SketchValue.closed_profile_entity_ids != (Membership,)
        or FeatureValue.attributes.get("fusion.profile_native_members") != Membership
    ):
        return None
    EntityIds = {Value.id for Value in SketchValue.entities}
    if len(EntityIds) != len(SketchValue.entities):
        return None
    Circle = None
    for Entity in SketchValue.entities:
        Geometry = Entity.geometry
        if Entity.fixed:
            return None
        if Entity.id == Membership[0]:
            if (
                Entity.construction
                or Entity.kind != GeometryKind.KCircle
                or not isinstance(Geometry, CircleGeometry)
            ):
                return None
            Circle = Geometry
        elif (
            Entity.kind != GeometryKind.KPoint
            or not isinstance(Geometry, PointGeometry)
            or not IsFinitePlane(Geometry.point)
        ):
            return None
    return Circle
