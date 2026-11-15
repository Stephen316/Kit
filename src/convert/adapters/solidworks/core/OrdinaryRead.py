from dataclasses import replace as Replace
from struct import error as StructError

from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import ArchiveError
from convert.adapters.solidworks.core.Native import (
    KPlaneSupportKind,
    DecodeNotices,
    IsPlaneFeature,
    NativeModel,
    NativePlane,
    NativeSketchA,
)
from convert.adapters.solidworks.resolved.RectanglePart import (
    RectanglePart,
    ReadRectPart,
)

# retained native references describe a typed support record rather than inferred feature order
KArchiveSupport = "typed-archive-reference"


# the neutral plane uses the orientation and record extent from its actual saved datum
def UpdateDatum(Plane: NativePlane, Parsed: RectanglePart) -> NativePlane:
    UAxis, VAxis, Normal = Parsed.Directions
    PointMetres = Parsed.Datum.Geometry.PointMetres
    return Replace(
        Plane,
        origin_mm=(PointMetres[0] * 1000, PointMetres[1] * 1000, PointMetres[2] * 1000),
        normal=Normal,
        u_axis=UAxis,
        v_axis=VAxis,
        native_offset=Parsed.Datum.Offset,
        native_length=Parsed.Datum.EndOffset - Parsed.Datum.Offset,
    )


# native feature identity must agree before the typed support can update an existing sketch
def AttachRectPlane(Model: NativeModel, Parsed: RectanglePart) -> NativeModel:
    Profile, Datum = Parsed.Profile, Parsed.Datum
    Sketches = tuple(
        Sketch
        for Sketch in Model.sketches
        if (Sketch.object_id, Sketch.name) == (Profile.FeatureId, Profile.NameValue)
    )
    Matches = tuple(
        Plane
        for Plane in Model.planes
        if Plane.principal
        and (Plane.object_id, Plane.name) == (Datum.FeatureId, Datum.NameValue)
    )
    if len(Sketches) != 1 or len(Matches) != 1:
        return Model
    (Owner,) = Sketches
    (SavedPlane,) = Matches
    Reference = Parsed.Reference
    TypedSupport = NativeSketchA(
        Reference.FeatureOffset,
        Reference.FeatureId,
        Reference.AxisCode,
        *Parsed.Directions,
        Reference.BasisOffset,
    )
    Update = Replace(
        Owner,
        support_plane_id=Datum.FeatureId,
        support_kind=KPlaneSupportKind,
        support_plane=TypedSupport,
        support_source=KArchiveSupport,
        unframed_support_plane_id=None,
    )
    Planes = tuple(
        UpdateDatum(Plane, Parsed) if Plane is SavedPlane else Plane
        for Plane in Model.planes
    )
    Result = tuple(Update if Sketch is Owner else Sketch for Sketch in Model.sketches)
    PlaneIds = {Plane.object_id for Plane in Planes}
    Unframed = tuple(
        Feature
        for Feature in Model.features
        if IsPlaneFeature(Feature)
        and Feature.native_offset is not None
        and Feature.object_id not in PlaneIds
    )
    return Replace(
        Model,
        planes=Planes,
        sketches=Result,
        diagnostics=DecodeNotices(Model.features, Unframed, Result),
    )


# existing imports keep their compatibility path when the archive shape is outside the typed scope
def ReadRectSupport(
    Model: NativeModel, ConfigData: bytes, Resolved: bytes, Generation: int | None
) -> NativeModel:
    if Generation != KConfigGen or not ConfigData:
        return Model
    try:
        Parsed = ReadRectPart(ConfigData, Resolved, Generation)
    except (ArchiveError, StructError):
        return Model
    return AttachRectPlane(Model, Parsed)
