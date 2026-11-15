from dataclasses import dataclass as Dataclass, replace as Replace
from math import dist as Distance

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectBindings import KPointToleranceMm
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.sketch.GeometryTypes import KPointId, PointReference
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumGeometry import GeometryKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.Transform import KOriginZero, Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordProvenance import ProvenanceSpan


# a projected dimension reference keeps both the local identity and earlier origin owner
@Dataclass(frozen=True, slots=True)
class CutOriginPoint:
    PointId: KPointId
    Entity: SketchEntity
    PickValue: Selection
    OwnerId: str


# the projected point must come from the typed and already reached origin feature
def ReadCutOrigin(
    Document: CadDocument, ProfileStep: FeatureStep, Source: CutRuleSource
) -> tuple[PointReference, FeatureStep]:
    Origin = Source.Origin
    References = Source.SketchData.Geometry["external_point_references"]
    RequireArch(len(References), 1, "one saved cut offset projection")
    (Reference,) = References
    RequireArch(
        (
            Reference["feature_id"],
            Reference["handle_class"],
            Reference["handle_fields"],
        ),
        (Origin.FeatureId, "sgPointHandle", (0, -1, 0)),
        "offset pair uses the reached Origin point",
    )
    Identity = f"sldprt:feature:{Origin.FeatureId}"
    Owners = [Value for Value in Document.feature_timeline if Value.id == Identity]
    RequireArch(len(Owners), 1, "unique neutral origin owner")
    (Owner,) = Owners
    RequireArch(
        (Owner.name, Owner.kind, Owner.suppressed, Owner.order < ProfileStep.order),
        (Origin.NameValue, FeatureKind.KReference, False, True),
        "active earlier origin point owner",
    )
    return Reference, Owner


# the local point cache must agree with projecting the saved origin through the face frame
def CutOriginCoord(
    Reference: PointReference,
    Frame: Transform,
    Source: CutRuleSource,
) -> PlaneVector:
    RequireArch(
        Source.Origin.Geometry.PointValue, (0, 0), "owned origin point location"
    )
    RequireArch(
        Source.Origin.Support.ShiftScale,
        (0, 0, 0, 1),
        "owned origin identity placement",
    )
    PointSlot, _ = Reference["local_id"]
    Geometry = Source.SketchData.Geometry
    RequireArch(
        Geometry["point_relation_tallies"][PointSlot]["id"],
        Reference["local_id"],
        "typed origin proxy member",
    )
    NativeX, NativeY = (1000 * Value for Value in Geometry["points_metres"][PointSlot])
    FrameDelta = SpaceVector(-Frame.origin.x, -Frame.origin.y, -Frame.origin.z)
    Expected = (
        DotVector(FrameDelta, Frame.x_axis),
        DotVector(FrameDelta, Frame.y_axis),
    )
    RequireArch(
        Distance((NativeX, NativeY), Expected) <= KPointToleranceMm,
        True,
        "cut frame projects the owned origin point",
    )
    return PlaneVector(NativeX, NativeY)


# the selection and construction point retain separate native point membership and source ownership
def MakeCutOrigin(
    SketchValue: Sketch,
    Reference: PointReference,
    Owner: FeatureStep,
    Coordinates: PlaneVector,
    Source: CutRuleSource,
) -> CutOriginPoint:
    PointSlot, NativeId = Reference["local_id"]
    PointOrigin = RectSource(
        str(NativeId),
        Source.ConfigStream,
        Source.SketchData.Members.Points[PointSlot],
        "cut-origin-proxy-point",
    )
    Geometry = Source.Origin.Geometry
    SpanValue = ProvenanceSpan(
        Source.ResolvedStream,
        Geometry.Offset,
        Geometry.EndOffset - Geometry.Offset,
        "origin-source-point",
    )
    Origin = Replace(PointOrigin, spans=(*PointOrigin.spans, SpanValue))
    PickValue = Selection(
        f"sldprt:selection:{Source.ProfileId}:origin:{Source.Origin.FeatureId}",
        f"{Owner.name} projected point",
        (SelectPathElem("feature", Owner.id, "point:0"),),
        query=FreezeMapping(
            {
                "kind": "projected_point",
                "role": "sketch_origin",
                "native_source_id": Source.Origin.FeatureId,
            }
        ),
        point=KOriginZero,
        provenance=Origin,
    )
    Entity = SketchEntity(
        f"{SketchValue.id}:native-point:{NativeId}",
        GeometryKind.KPoint,
        PointGeometry(Coordinates),
        construction=True,
        fixed=True,
        provenance=Origin,
        attributes=FreezeMapping(
            {
                "native_point_id": Reference["local_id"],
                "native_origin_feature_id": Source.Origin.FeatureId,
                "native_origin_feature_time": Reference["feature_time"],
                "native_origin_point_handle": Reference["handle_fields"],
                "solidworks.projection_source_selection_id": PickValue.id,
            }
        ),
    )
    return CutOriginPoint(Reference["local_id"], Entity, PickValue, Owner.id)
