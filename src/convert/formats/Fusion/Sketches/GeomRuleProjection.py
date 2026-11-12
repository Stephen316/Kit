from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Geometric.GeomRuleAttach import AttachGeomRule
from convert.formats.Fusion.Sketches.SketchRuleIds import ReadSketchRules
from convert.formats.Fusion.Sketches.SketchRuleScope import (
    IndexRuleEnts,
    ReadSketchRoot,
)
from interchange.geometry.models.Sketch import Sketch, SketchRelation
from interchange.records.RecordDiagnostic import Diagnostic


# source scope failures remain visible without removing independently valid relations
def ProjectRules(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchValue: Sketch
) -> tuple[tuple[SketchRelation, ...], tuple[Diagnostic, ...]]:
    try:
        RootSpan = ReadSketchRoot(SketchValue, Owners)
        Members, _ = ReadSketchRules(BulkData, RootSpan)
        if not Members:
            return (), ()
        Entities = IndexRuleEnts(BulkData, Owners, SketchValue, RootSpan.ObjectId)
    except ValueError as ErrorInfo:
        return (), (
            Diagnostic(
                code="fusion.sketch.constraint.scope",
                message=str(ErrorInfo),
                entity_id=SketchValue.id,
                provenance=SketchValue.provenance,
            ),
        )
    Relations: list[SketchRelation]
    Diagnostics: list[Diagnostic]
    Relations, Diagnostics = [], []
    for MemberId in Members:
        SpanValue = Owners.get(MemberId)
        try:
            if SpanValue is None:
                raise ValueError("Fusion geometric relation record is missing")
            Relations.append(AttachGeomRule(BulkData, SpanValue, RootSpan, Entities))
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.sketch.constraint.unsupported",
                    message=str(ErrorInfo),
                    entity_id=SketchValue.id,
                    provenance=(
                        RecordOrigin(SpanValue)
                        if SpanValue is not None
                        else SketchValue.provenance
                    ),
                )
            )
    return tuple(Relations), tuple(Diagnostics)


# only relations reciprocally owned by projected sketches enter the neutral document
def BuildGeomRules(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Sketches: tuple[Sketch, ...],
) -> tuple[dict[str, tuple[SketchRelation, ...]], tuple[Diagnostic, ...]]:
    if not Sketches:
        return {}, ()
    Records = tuple(SpanValue for SpanValue in Spans if SpanValue.IsPrimary)
    Owners = {SpanValue.ObjectId: SpanValue for SpanValue in Records}
    if len(Owners) != len(Records):
        return {}, (
            Diagnostic(
                code="fusion.sketch.constraint.scope",
                message="Ambiguous native Fusion sketch relation records",
            ),
        )
    Result: dict[str, tuple[SketchRelation, ...]] = {}
    Diagnostics: list[Diagnostic] = []
    for SketchValue in Sketches:
        Relations, Issues = ProjectRules(BulkData, Owners, SketchValue)
        Result[SketchValue.id] = Relations
        Diagnostics.extend(Issues)
    return Result, tuple(Diagnostics)
