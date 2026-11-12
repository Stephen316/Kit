from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.Scales.ConstructionCenter import (
    CheckCenterPt,
    ReadWorkPoint,
)
from convert.formats.Fusion.Scales.OriginCenter import KWorkPoint, ReadOriginPt
from convert.formats.Fusion.Scales.PointBackend import ReadPointBack
from convert.formats.Fusion.Scales.SketchCenter import ReadSketchPt
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem, Selection


# a scale center must have a qualified local point identity before its cache is used
def ReadScaleCenter(
    BulkData: bytes,
    Context: InputContext,
    Document: CadDocument,
    Receiver: FeatureStep,
    Scope: CreatorScope,
    FeatureId: int,
    BackendId: int,
) -> Selection:
    Owners = Context.Owners
    Cached, Method, Descriptor = ReadPointBack(BulkData, Owners, BackendId, FeatureId)
    if Method not in (9, 10):
        raise ValueError("Unsupported Fusion Scale center source method")
    LeafId = ReadDescLeaf(BulkData, Owners, Descriptor, FeatureId)
    PathElems: tuple[SelectPathElem, ...] = ()
    Query: dict[str, object] = {"native_component_id": Scope.ComponentId}
    if Method == 10:
        Point, SketchValue, Entity = ReadSketchPt(
            BulkData, Context, Document, Receiver, Scope, LeafId
        )
        PathElems = (
            SelectPathElem("sketch", SketchValue.id),
            SelectPathElem("sketch_entity", Entity.id),
        )
        Query["kind"] = "sketch_point"
    else:
        PointId = ReadEntityLeaf(BulkData, Owners, LeafId)
        SpanValue = Owners.get(PointId)
        if SpanValue is None or SpanValue.ClassGuid != KWorkPoint:
            raise ValueError("Missing typed Fusion Scale construction point")
        Query["native_point_id"] = PointId
        if SpanValue.EndOffset - SpanValue.PayloadOffset == 150:
            Point = ReadOriginPt(BulkData, Owners, PointId, Scope.ComponentId)
            Query["kind"] = "component_origin_point"
        else:
            Point, SourceId, SketchId, EntityId = ReadWorkPoint(
                BulkData, Context, Document, Receiver, Scope, PointId
            )
            Query.update(
                kind="construction_point",
                source_feature_id=SourceId,
                support_sketch_id=SketchId,
                support_point_id=EntityId,
            )
    CheckCenterPt(Point, Cached)
    return Selection(
        id=f"fusion-scale-center-{Context.HistoryId}-{FeatureId}",
        name="Scale center",
        path=PathElems,
        query=FreezeMapping(Query),
        point=Point,
        provenance=ParamOrigin(Owners[Descriptor]),
        attributes=FreezeMapping(
            {"fusion.center_backend_id": BackendId, "fusion.center_terminal_id": LeafId}
        ),
    )
