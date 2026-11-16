from dataclasses import replace as Replace

from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.Profiles.RectControls.AttachRectCtrl import AttachRectCtrl
from convert.Formats.Fusion.Profiles.RectControls.CheckRectGraph import CheckRectGraph
from convert.Formats.Fusion.Profiles.RectControls.ProjectPartRect import ProjectPartRect
from convert.Formats.Fusion.Profiles.RectControls.SketchDimRows import ReadSketchDims
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.CenterDeps.CenterPair import FindCenterPair
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordDiagnostic import Diagnostic


# the two selected rectangles share one native graph and publish their contour joins together
def ProjectRectCtrl(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
) -> CadDocument:
    PairValue = FindCenterPair(Document)
    if PairValue is None:
        return ProjectPartRect(Document, BulkData, Spans, History)
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Params = {Value.id: Value for Value in Document.parameters}
    try:
        BossRows = ReadSketchDims(BulkData, Owners, PairValue.BossSketch, Params, 2)
        CutRows = ReadSketchDims(BulkData, Owners, PairValue.CutSketch, Params, 4)
        GraphSpan = CheckRectGraph(
            BulkData, Owners, History.OwnerId, BossRows + CutRows
        )
        BossSketch = AttachRectCtrl(
            BulkData,
            Owners,
            PairValue.BossSketch,
            PairValue.BossStep,
            BossRows,
            GraphSpan,
        )
        CutSketch = AttachRectCtrl(
            BulkData,
            Owners,
            PairValue.CutSketch,
            PairValue.CutterStep,
            CutRows,
            GraphSpan,
        )
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.profile.rectangle_controls.unsupported",
                    message=str(ErrorInfo),
                    entity_id=PairValue.CutSketch.id,
                    provenance=PairValue.CutSketch.provenance,
                ),
            ),
        )
    Sketches = {Value.id: Value for Value in (BossSketch, CutSketch)}
    return Replace(
        Document,
        sketches=tuple(Sketches.get(Value.id, Value) for Value in Document.sketches),
    )
