from dataclasses import replace as Replace

from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.Profiles.RectControls.AttachRectCtrl import AttachRectCtrl
from convert.formats.Fusion.Profiles.RectControls.CheckRectGraph import CheckRectGraph
from convert.formats.Fusion.Profiles.RectControls.FindPartRect import FindPartRect
from convert.formats.Fusion.Profiles.RectControls.SketchDimRows import ReadSketchDims
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordDiagnostic import Diagnostic


# a principal rectangle preserves side evidence under its actual sketch or consuming profile
def ProjectPartRect(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
) -> CadDocument:
    PartValue = FindPartRect(Document, History)
    if PartValue is None:
        return Document
    SketchValue, Feature = PartValue
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Params = {Value.id: Value for Value in Document.parameters}
    try:
        DimRows = ReadSketchDims(BulkData, Owners, SketchValue, Params, 2)
        GraphSpan = CheckRectGraph(BulkData, Owners, History.OwnerId, DimRows)
        Verified = AttachRectCtrl(
            BulkData, Owners, SketchValue, Feature, DimRows, GraphSpan
        )
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.profile.rectangle_controls.unsupported",
                    message=str(ErrorInfo),
                    entity_id=SketchValue.id,
                    provenance=SketchValue.provenance,
                ),
            ),
        )
    return Replace(Document, sketches=(Verified,))
