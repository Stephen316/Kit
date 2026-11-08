# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose

from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


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


# a verified native point identity lets freecad move the profile and its center together
def GetCenterPoint(SketchValue: Sketch) -> SketchEntity | None:
    if (
        len(SketchValue.closed_profile_entity_ids) != 1
        or len(SketchValue.closed_profile_entity_ids[0]) != 1
        or SketchValue.provenance is None
        or SketchValue.provenance.adapter != "fusion.f3d"
        or SketchValue.attributes.get("freecad")
    ):
        return None
    Selected = SketchValue.closed_profile_entity_ids[0][0]
    Circle = next(
        (Value for Value in SketchValue.entities if Value.id == Selected), None
    )
    if Circle is None or not isinstance(Circle.geometry, CircleGeometry):
        return None
    NativeId = Circle.attributes.get("fusion.circle_native_center_id")
    if type(NativeId) is not int or NativeId <= 0:
        return None
    PointId = f"fusion-sketch-entity-{NativeId}"
    return next(
        (
            Value
            for Value in SketchValue.entities
            if Value.id == PointId
            and isinstance(Value.geometry, PointGeometry)
            and IsClose(
                Value.geometry.point.x,
                Circle.geometry.center.x,
                abs_tol=1e-8,
                rel_tol=0.0,
            )
            and IsClose(
                Value.geometry.point.y,
                Circle.geometry.center.y,
                abs_tol=1e-8,
                rel_tol=0.0,
            )
        ),
        None,
    )
