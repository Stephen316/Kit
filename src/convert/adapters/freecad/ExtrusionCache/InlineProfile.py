from collections.abc import Mapping

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.Transform import Transform
from interchange.serialization.WireData import ValidateWireMap

# initial shape generation covers the exact analytic profile families already serialized without a kernel
KCacheProfile = CircleGeometry | tuple[LineGeometry, ...]


# explicit loop membership separates the actual face from construction and helper geometry
def ReadCacheLoop(SketchValue: Sketch) -> KCacheProfile | None:
    if SketchValue.suppressed or len(SketchValue.closed_profile_entity_ids) != 1:
        return None
    (Members,) = SketchValue.closed_profile_entity_ids
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    if len(set(Members)) != len(Members) or any(
        Member not in Entities for Member in Members
    ):
        return None
    Selected = tuple(Entities[Member] for Member in Members)
    if any(Entity.construction for Entity in Selected):
        return None
    if len(Selected) == 1 and isinstance(Selected[0].geometry, CircleGeometry):
        return Selected[0].geometry
    Lines = tuple(
        Entity.geometry
        for Entity in Selected
        if isinstance(Entity.geometry, LineGeometry)
    )
    return Lines if 3 <= len(Lines) == len(Selected) <= 64 else None


# cached coordinates follow the same millimetre rigid support frame as the emitted sketch
def ReadCacheFrame(
    Manifest: Mapping[str, object], FeatureId: str
) -> tuple[Transform, KCacheProfile] | None:
    Document = CadDocument.from_dict(ValidateWireMap(Manifest))
    if Document.units != UnitSystem.KMillimeter:
        return None
    (Feature,) = (Value for Value in Document.feature_timeline if Value.id == FeatureId)
    if not isinstance(Feature.definition, ExtrudeFeature):
        return None
    (SketchValue,) = (
        Value for Value in Document.sketches if Value.id == Feature.sketch_id
    )
    (PlaneValue,) = (
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    if (
        PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
    ):
        return None
    Profile = ReadCacheLoop(SketchValue)
    return (PlaneValue.transform, Profile) if Profile is not None else None
