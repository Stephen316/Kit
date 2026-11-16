from dataclasses import replace as Replace
from math import dist as Distance

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectBindings import (
    KPointToleranceMm,
    BoundRectEdge,
    RectBindings,
)
from convert.adapters.solidworks.Core.RectOrigin import RectOrigin
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector


# neutral edge orientation comes from its persistent loop while coordinates come from the saved points
def ProjectRectEdge(
    Bound: BoundRectEdge, Binding: RectBindings, FeatureId: int, StreamName: str
) -> SketchEntity:
    FirstSlot, EndSlot = Bound.Slots
    NativeId = Bound.Source["native_id"]
    return Replace(
        Bound.Entity,
        geometry=LineGeometry(
            PlaneVector(*Binding.Points[FirstSlot]),
            PlaneVector(*Binding.Points[EndSlot]),
        ),
        provenance=RectSource(
            f"{FeatureId}:{NativeId}",
            StreamName,
            Bound.SpanValue,
            "sketch-profile-line",
        ),
        attributes=FreezeMapping(
            {
                **Bound.Entity.attributes,
                "native_segment_id": NativeId,
                "native_member_index": Bound.Source["member_index"],
                "native_point_indices": tuple(Bound.Source["point_indices"]),
            }
        ),
    )


# typed positions preserve public point identities and distinguish the foreign origin proxy
def ProjectRectPt(
    Profile: ProfileSketch,
    Binding: RectBindings,
    Origin: RectOrigin,
    SlotValue: int,
    StreamName: str,
) -> SketchEntity:
    Entity = Binding.PointEntities[SlotValue]
    Coordinates = Binding.Points[SlotValue]
    PointId = Profile.Geometry["point_relation_tallies"][SlotValue]["id"]
    IsProxy = PointId == Origin.Proxy["local_id"]
    Attributes: dict[str, object] = {**Entity.attributes, "native_point_id": PointId}
    if IsProxy:
        Attributes = {
            "native_point_id": PointId,
            "native_origin_feature_id": Origin.Proxy["feature_id"],
            "native_origin_point_handle": Origin.Proxy["handle_fields"],
        }
    else:
        Geometry = Entity.geometry
        if not isinstance(Geometry, PointGeometry):
            raise ArchiveError("Typed rectangle corner has no stable point entity")
        RequireArch(
            Distance(Coordinates, (Geometry.point.x, Geometry.point.y))
            <= KPointToleranceMm,
            True,
            "typed corner matches its public point",
        )
    return Replace(
        Entity,
        kind=GeometryKind.KPoint,
        geometry=PointGeometry(PlaneVector(*Coordinates)),
        construction=True if IsProxy else Entity.construction,
        fixed=True if IsProxy else Entity.fixed,
        provenance=RectSource(
            f"{Profile.FeatureId}:{PointId[1]}",
            StreamName,
            Profile.Members.Points[SlotValue],
            "sketch-point",
        ),
        attributes=FreezeMapping(Attributes),
    )
