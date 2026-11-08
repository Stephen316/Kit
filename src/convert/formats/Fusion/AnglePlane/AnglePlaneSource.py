# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace
from math import hypot as Hypot

from convert.formats.Fusion.AnglePlane.AngleBackend import ReadAngleBack
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import (
    IsSameAngPlane,
    RotatePlane,
    VectorCoords,
)
from convert.formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.formats.Fusion.Extrudes.Plane.OffsetOrigin import ReadOffsetOrg
from convert.formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.formats.Fusion.PlaneCollection import ReadPlaneComp
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import ReadOriginAxis
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# reciprocal source links independently regenerate the cached angular datum
def AttachAngleDef(
    BulkData: bytes, Owners: dict[int, RecordSpan], PlaneValue: SupportPlane
) -> SupportPlane:
    Origin = PlaneValue.provenance
    if Origin is None or PlaneValue.attributes.get("fusion.cached_plane_mode") != 2:
        return PlaneValue
    FeatureId = int(PlaneValue.attributes["fusion.feature_object_id"])
    Backend, Extra, Angle, AxisDesc, BaseDesc = ReadAngleBack(
        BulkData, Owners, FeatureId, int(Origin.native_id)
    )
    Component, Collection = ReadPlaneComp(BulkData, Owners, PlaneValue)
    AxisLeaf = ReadDescLeaf(BulkData, Owners, AxisDesc, FeatureId)
    BaseLeaf = ReadDescLeaf(BulkData, Owners, BaseDesc, FeatureId)
    AxisId = ReadEntityLeaf(BulkData, Owners, AxisLeaf)
    BaseId = ReadEntityLeaf(BulkData, Owners, BaseLeaf)
    _, AxisOrigin, AxisValue, Container = ReadOriginAxis(
        BulkData, Owners, AxisId, Component
    )
    BaseFrame, BaseContainer = ReadOffsetOrg(BulkData, Owners, BaseId, Component)
    OffsetParam = CheckExtBinding(BulkData, Owners, FeatureId, Extra, "ExtraOffset")
    AngleParam = CheckExtBinding(BulkData, Owners, FeatureId, Angle, "RotateAngle")
    if (
        Container != BaseContainer
        or ParamQuantity(OffsetParam).unit != "cm"
        or OffsetParam.Number != 0.0
        or ParamQuantity(AngleParam).unit != "rad"
    ):
        raise ValueError("Unsupported Fusion Angle plane controls or support")
    ZeroFrame = ReadPlaneBasis(PlaneValue.transform, BaseFrame, AxisOrigin, AxisValue)
    if not IsSameAngPlane(
        RotatePlane(ZeroFrame, AngleParam.Number), PlaneValue.transform
    ):
        raise ValueError("Fusion Angle plane authored rotation disagrees with cache")
    Records = (
        Backend,
        Extra,
        Angle,
        AxisDesc,
        AxisLeaf,
        AxisId,
        BaseDesc,
        BaseLeaf,
        BaseId,
        Container,
        Collection,
    )
    return Replace(
        PlaneValue,
        attributes=FreezeMapping(
            {
                **PlaneValue.attributes,
                "fusion.angle_plane": FreezeMapping(
                    {
                        "component_id": Component,
                        "axis_object_id": AxisId,
                        "base_object_id": BaseId,
                        "angle_binding_id": Angle,
                        "offset_binding_id": Extra,
                        "zero_origin": VectorCoords(ZeroFrame.origin),
                        "zero_axis": VectorCoords(ZeroFrame.x_axis),
                        "zero_normal": VectorCoords(ZeroFrame.z_axis),
                    }
                ),
            }
        ),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + tuple(ParamOrigin(Owners[Identity]).spans[0] for Identity in Records),
        ),
    )


# retaining the pivot on its authored axis keeps placement and limiting geometry independent
def ReadPlaneBasis(
    Cached: Transform,
    BaseFrame: Transform,
    AxisOrigin: SpaceVector,
    AxisValue: SpaceVector,
) -> Transform:
    Offset = OffsetVector(Cached.origin, AxisOrigin, -1.0)
    if (
        Hypot(*VectorCoords(CrossVector(Offset, AxisValue))) > 1e-8
        or abs(DotVector(BaseFrame.z_axis, AxisValue)) > 1e-9
    ):
        raise ValueError("Fusion Angle plane base or pivot misses its axis")
    return Transform(
        Cached.origin,
        AxisValue,
        CrossVector(BaseFrame.z_axis, AxisValue),
        BaseFrame.z_axis,
    )
