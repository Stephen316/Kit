from dataclasses import replace as Replace
from math import hypot as Hypot

from convert.Formats.Fusion.AnglePlane.AngleBackend import ReadAngleBack
from convert.Formats.Fusion.AnglePlane.AnglePlaneBasis import (
    IsSameAngPlane,
    RotatePlane,
    VectorCoords,
)
from convert.Formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.Formats.Fusion.Extrudes.Plane.OffsetOrigin import ReadOffsetOrg
from convert.Formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.Formats.Fusion.PlaneCollection import ReadPlaneComp
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.OriginAxis import ReadOriginAxis
from convert.Formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# reciprocal source links independently regenerate the cached angular datum
def ReadAngleDef(
    BulkData: bytes, Owners: dict[int, RecordSpan], PlaneValue: SupportPlane
) -> tuple[SupportPlane, Transform, int, int, int]:
    Origin = PlaneValue.provenance
    if Origin is None or PlaneValue.attributes.get("fusion.cached_plane_mode") != 2:
        raise ValueError("Fusion construction plane is not an angular datum")
    FeatureId = PlaneValue.attributes["fusion.feature_object_id"]
    if type(FeatureId) is not int:
        raise ValueError("Fusion angular datum has no native feature identity")
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
    Qualified = Replace(
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
    return Qualified, ZeroFrame, Angle, Extra, Component


# existing frame consumers retain the same source evidence without new dependencies
def AttachAngleDef(
    BulkData: bytes, Owners: dict[int, RecordSpan], PlaneValue: SupportPlane
) -> SupportPlane:
    if (
        PlaneValue.provenance is None
        or PlaneValue.attributes.get("fusion.cached_plane_mode") != 2
    ):
        return PlaneValue
    return ReadAngleDef(BulkData, Owners, PlaneValue)[0]


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
