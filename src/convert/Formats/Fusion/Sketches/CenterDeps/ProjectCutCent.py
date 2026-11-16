from dataclasses import replace as Replace

from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.CenterDeps.CenterPair import FindCenterPair
from convert.Formats.Fusion.Sketches.CenterDeps.KeepCutOrigin import KeepCutOrigin
from convert.Formats.Fusion.Sketches.CenterDeps.LinkCenterDims import LinkCenterDims
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordDiagnostic import Diagnostic


# a refused expression must leave independently verified native origin evidence intact
def ProjectCutCent(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
) -> CadDocument:
    SketchedPair = FindCenterPair(Document)
    if SketchedPair is None:
        return Document
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    try:
        Origin = KeepCutOrigin(
            BulkData,
            Owners,
            SketchedPair.CutSketch,
            SketchedPair.Frame,
            SketchedPair.BodyId,
            SketchedPair.ComponentId,
        )
        CutSketch = Replace(
            SketchedPair.CutSketch,
            entities=tuple(
                Origin if Value.id == Origin.id else Value
                for Value in SketchedPair.CutSketch.entities
            ),
        )
        Document = Replace(
            Document,
            sketches=tuple(
                CutSketch if Value.id == CutSketch.id else Value
                for Value in Document.sketches
            ),
        )
        return LinkCenterDims(Document, BulkData, Spans, History, SketchedPair, Origin)
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.sketch.center_dependencies.unsupported",
                    message=str(ErrorInfo),
                    entity_id=SketchedPair.CutSketch.id,
                    provenance=SketchedPair.CutSketch.provenance,
                ),
            ),
        )
