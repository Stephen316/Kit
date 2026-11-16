from dataclasses import replace as Replace

from convert.Formats.Fusion.Extrudes.Cut.AttachCutEnd import AttachCutEnd
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordDiagnostic import Diagnostic


# the partial reader can attach saved cut semantics after verifying the body target
def ProjectCutEnds(
    Document: CadDocument, BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> CadDocument:
    Candidates = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.kind == FeatureKind.KExtrusion
        and Value.operation == BooleanOp.KCutOperation
        and Value.definition is None
    )
    if not Candidates:
        return Document
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Params = {Value.id: Value for Value in Document.parameters}
    Selections = {Value.id: Value for Value in Document.selections}
    Frames = {Value.id: Value for Value in Document.support_planes}
    SketchFrames = {
        Value.id: Frames[Value.support_plane_id] for Value in Document.sketches
    }
    Updated: dict[str, FeatureStep] = {}
    ExtentPicks: list[Selection] = []
    Issues: list[Diagnostic] = []
    for StepValue in Candidates:
        Frame = SketchFrames.get(StepValue.sketch_id or "")
        Targets = tuple(
            Selections[Identity]
            for Identity in StepValue.selection_ids
            if Selections[Identity].query.get("kind") == "historical_body"
            and Selections[Identity].query.get("role") == "target"
        )
        if Frame is None or len(Targets) != 1:
            continue
        try:
            NewStep, Extent = AttachCutEnd(
                BulkData, Owners, StepValue, Params, Frame, Targets[0]
            )
        except ValueError as ErrorInfo:
            Issues.append(
                Diagnostic(
                    code="fusion.extrude.cut_unsupported",
                    message=str(ErrorInfo),
                    entity_id=StepValue.id,
                    provenance=StepValue.provenance,
                )
            )
            continue
        Updated[StepValue.id] = NewStep
        if Extent is not None:
            ExtentPicks.append(Extent)
    return Replace(
        Document,
        feature_timeline=tuple(
            Updated.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        selections=Document.selections + tuple(ExtentPicks),
        diagnostics=tuple(
            Value
            for Value in Document.diagnostics
            if Value.code != "fusion.extrude.unsupported"
            or Value.entity_id not in Updated
        )
        + tuple(Issues),
    )
