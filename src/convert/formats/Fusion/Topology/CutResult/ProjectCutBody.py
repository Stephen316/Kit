from collections.abc import Callable
from dataclasses import replace as Replace

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.CutResult.AttachCutBody import AttachCutBody
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.records.RecordDiagnostic import Diagnostic


# saved pocket topology is a partial result observation tied to one terminal cut
def ProjectCutBody(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    if (
        Document.assembly is not None
        or Document.bodies
        or Document.brep is not None
        or not Document.feature_timeline
    ):
        return Document
    Cutter = Document.feature_timeline[-1]
    Definition = Cutter.definition
    if Cutter.operation != BooleanOp.KCutOperation or not isinstance(
        Definition, ExtrudeFeature
    ):
        return Document
    FaceCount = {ExtrudeEnd.KBlind.value: 11, ExtrudeEnd.KThroughAll.value: 10}.get(
        Definition.end_condition
    )
    Sketches = {Value.id: Value for Value in Document.sketches}
    SketchValue = Sketches.get(Cutter.sketch_id or "")
    if FaceCount is None or SketchValue is None:
        return Document
    Frames = {Value.id: Value for Value in Document.support_planes}
    Frame = Frames[SketchValue.support_plane_id]
    Selections = {Value.id: Value for Value in Document.selections}
    Support = Selections.get(Frame.support_selection_id or "")
    if (
        Frame.attributes.get("fusion.native_support_kind")
        != "historical_face_occurrence"
        or Support is None
    ):
        return Document
    try:
        return AttachCutBody(
            Document, BulkData, Spans, Cutter, Definition, Support, FaceCount, LoadBlob
        )
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.cut.saved_body.unsupported",
                    message=str(ErrorInfo),
                    entity_id=Cutter.id,
                    provenance=Cutter.provenance,
                ),
            ),
        )
