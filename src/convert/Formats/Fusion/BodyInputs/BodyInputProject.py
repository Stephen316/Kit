from dataclasses import replace as Replace

from convert.Formats.Fusion.BodyInputs.InputContext import ReadInputScope
from convert.Formats.Fusion.BodyInputs.InputReaders import KBodyInputReaders
from convert.Formats.Fusion.BodyInputs.InputStep import ReadBodyInputs
from convert.Formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordDiagnostic import Diagnostic


# an unsupported operand leaves the original native step and remaining timeline intact
def BodyInputIssue(StepValue: FeatureStep, Message: str) -> Diagnostic:
    return Diagnostic(
        code="fusion.body_inputs.unsupported",
        message=Message,
        entity_id=StepValue.id,
        provenance=StepValue.provenance,
    )


# the public projection attaches verified operands without asserting regenerated feature geometry
def ProjectPicks(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
) -> CadDocument:
    Candidates = tuple(
        (Index, StepValue, int(Origin.native_id))
        for Index, StepValue in enumerate(Document.feature_timeline)
        if (Origin := StepValue.provenance) is not None
        and Origin.spans
        and Origin.spans[0].record_kind in KBodyInputReaders
    )
    if not Candidates:
        return Document
    try:
        Context = ReadInputScope(BulkData, Spans, History, Document.feature_timeline)
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + tuple(
                BodyInputIssue(StepValue, str(ErrorInfo))
                for _, StepValue, _ in Candidates
            ),
        )
    Steps = list(Document.feature_timeline)
    Picks: list[Selection] = []
    Issues: list[Diagnostic] = []
    for Index, StepValue, FeatureId in Candidates:
        try:
            if not IsSavedActive(StepValue):
                continue
            Steps[Index], Inputs = ReadBodyInputs(
                BulkData, Context, FeatureId, StepValue
            )
            Picks.extend(Inputs)
        except ValueError as ErrorInfo:
            Issues.append(BodyInputIssue(StepValue, str(ErrorInfo)))
    if not Picks and not Issues:
        return Document
    return Replace(
        Document,
        feature_timeline=tuple(Steps),
        selections=Document.selections + tuple(Picks),
        diagnostics=Document.diagnostics + tuple(Issues),
        capabilities=(
            Document.capabilities | {Capability.KSelections}
            if Picks
            else Document.capabilities
        ),
    )
