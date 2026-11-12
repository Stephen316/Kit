from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPrimitive import KSketchKinds, ReadPrimitive
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.records.RecordDiagnostic import Diagnostic


# sketch entities are grouped by verified owner references before resolving endpoints
def GroupGeometry(
    BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> dict[int, list[RecordSpan]]:
    Geometry: dict[int, list[RecordSpan]] = {}
    for SpanValue in Spans:
        if not SpanValue.IsPrimary or SpanValue.ClassGuid not in KSketchKinds:
            continue
        Cursor = MetaCursor(BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset])
        Cursor.Offset = len(Cursor.DataValue) - 11
        try:
            OwnerId = ReadNativeRef(Cursor)
        except ValueError:
            continue
        Geometry.setdefault(OwnerId, []).append(SpanValue)
    return Geometry


# point evidence precedes curves even when their native records arrive later
def ProjectGeom(
    BulkData: bytes, Records: list[RecordSpan]
) -> tuple[tuple[SketchEntity, ...], tuple[Diagnostic, ...]]:
    Points: dict[int, PlaneVector] = {}
    Entities: dict[int, SketchEntity] = {}
    Diagnostics: list[Diagnostic] = []
    for SpanValue in sorted(Records, key=PointFirst):
        BodyValue = BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
        try:
            Entity = ReadPrimitive(BodyValue, SpanValue, Points)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.sketch.primitive",
                    message=str(ErrorInfo),
                    provenance=RecordOrigin(SpanValue),
                )
            )
            continue
        Entities[SpanValue.ObjectId] = Entity
        if isinstance(Entity.geometry, PointGeometry):
            Points[SpanValue.ObjectId] = Entity.geometry.point
    return tuple(
        Entities[SpanValue.ObjectId]
        for SpanValue in Records
        if SpanValue.ObjectId in Entities
    ), tuple(Diagnostics)


# endpoint validation requires point records before other primitives
def PointFirst(SpanValue: RecordSpan) -> int:
    return 0 if SpanValue.ClassGuid == "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB" else 1
