from math import dist as Distance

from convert.Formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.Formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.Formats.Fusion.Extrudes.Plane.NativePlaneExt import NativePlaneExt
from convert.Formats.Fusion.Extrudes.Plane.OffsetBackend import (
    CheckOffsetDef,
    VectorCoords,
)
from convert.Formats.Fusion.Extrudes.Plane.PlaneExtControl import ReadPlaneCtrl
from convert.Formats.Fusion.Extrudes.Plane.PlaneExtNumeric import CheckPlaneNums
from convert.Formats.Fusion.Extrudes.Plane.PlaneExtPick import CheckPlanePick
from convert.Formats.Fusion.NativePlane import KPlaneFeature, ReadNativePlane
from convert.Formats.Fusion.PlaneCollection import ReadPlaneComp
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadEntityRef
from interchange.geometry.Models.SupportPlane import SupportPlane


# exact native controls and owned offset planes support selected plane extrusion projection
def ReadPlaneExt(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    Planes: dict[int, SupportPlane],
) -> NativePlaneExt:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    Fields = ReadPlaneCtrl(Cursor)
    ProfileId, ProfileProxy = ReadExtProfile(
        BulkData, Owners, Cursor, FeatureId, "one_sided"
    )
    CheckPlaneNums(BulkData, Owners, FeatureId, Fields)
    SelectionIds = ReadEntityRef(BulkData, Owners, Fields.ProxyId, FeatureId)
    PlaneId = SelectionIds[2]
    Plane = Planes.get(PlaneId)
    PlaneFeatureId = (
        None if Plane is None else Plane.attributes.get("fusion.feature_object_id")
    )
    if Plane is None or type(PlaneFeatureId) is not int:
        raise ValueError("Missing owned Fusion construction plane for Extrude")
    PlaneFeature = Owners.get(PlaneFeatureId)
    if PlaneFeature is None or PlaneFeature.ClassGuid != KPlaneFeature:
        raise ValueError("Missing Fusion selected plane creator")
    Cached = ReadNativePlane(BulkData, PlaneFeature, Owners)
    if (
        Cached.provenance is None
        or int(Cached.provenance.native_id) != PlaneId
        or Cached.attributes.get("fusion.cached_plane_mode") != 1
        or Plane.id != Cached.id
        or Plane.transform != Cached.transform
        or Distance(Fields.Direction, VectorCoords(Cached.transform.z_axis)) > 1e-10
    ):
        raise ValueError(
            "Fusion selected plane does not match the Extrude component frame"
        )
    ComponentId, CollectionId = ReadPlaneComp(BulkData, Owners, Cached)
    SelectorIds = CheckPlanePick(
        BulkData,
        Owners,
        Fields.ProxyId,
        SelectionIds,
        PlaneFeatureId,
        Cached.transform,
    )
    DefinitionIds = CheckOffsetDef(
        BulkData, Owners, PlaneId, PlaneFeatureId, ComponentId, Cached.transform
    )
    Evidence = tuple(
        dict.fromkeys(
            (
                ProfileProxy,
                Fields.CacheId,
                *SelectorIds,
                PlaneId,
                PlaneFeatureId,
                CollectionId,
                *DefinitionIds,
            )
        )
    )
    return NativePlaneExt(
        Fields.Role,
        PlaneId,
        Fields.ProxyId,
        ProfileId,
        ProfileProxy,
        Fields.OffsetId,
        Fields.AlongId,
        Fields.TaperId,
        Fields.Direction,
        Cursor.Offset,
        ComponentId,
        PlaneFeatureId,
        Evidence,
    )
