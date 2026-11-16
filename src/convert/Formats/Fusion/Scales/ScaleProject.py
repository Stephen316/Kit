from collections.abc import Callable
from dataclasses import replace as Replace

from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Scales.ScaleSnapshot import ReadScaleSnap
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Records.RecordDiagnostic import Diagnostic


# a failed cache proof retains earlier historical selections and feature timeline
def ProjectScale(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    if Document.assembly is not None or not Document.feature_timeline:
        return Document
    Feature = Document.feature_timeline[-1]
    if (
        Feature.kind != FeatureKind.KScale
        or Feature.provenance is None
        or not Feature.selection_ids
    ):
        return Document
    try:
        return ReadScaleSnap(
            Document,
            BulkData,
            Spans,
            History,
            Feature,
            int(Feature.provenance.native_id),
            LoadBlob,
        )
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.scale.body_unsupported",
                    message=str(ErrorInfo),
                    entity_id=Feature.id,
                    provenance=Feature.provenance,
                ),
            ),
        )
