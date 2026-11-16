from dataclasses import replace as Replace

from convert.Formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.CenterDeps.BindCenterExpr import BindCenterExpr
from convert.Formats.Fusion.Sketches.CenterDeps.CenterPair import CenterPair
from convert.Formats.Fusion.Sketches.CenterDeps.CheckCenterRim import CheckCenterRim
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import SketchEntity


# both center bindings must pass together against the same reciprocal parameter registry
def LinkCenterDims(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    SketchedPair: CenterPair,
    Origin: SketchEntity,
) -> CadDocument:
    _, Collection, Registry, _, Names = ReadPartScope(BulkData, Spans, History)
    Params = {Value.id: Value for Value in Document.parameters}
    if {
        f"fusion-parameter-{Identity}": NameValue
        for Identity, NameValue in Names.items()
    } != {Value.id: Value.name for Value in Document.parameters}:
        raise ValueError("Fusion Cut center parameter registry and projection disagree")
    Midpoint, Relations = CheckCenterRim(SketchedPair.CutSketch, Origin)
    if Midpoint.provenance is None or Origin.provenance is None:
        raise ValueError("Fusion Cut center lacks its native geometry witness")
    Proof = (
        ParamOrigin(Collection).spans
        + ParamOrigin(Registry).spans
        + Midpoint.provenance.spans
        + Origin.provenance.spans
    )
    Values = tuple(
        BindCenterExpr(Value, SketchedPair.BossSketch, Params, Proof)
        for Value in Relations
    )
    Updates = {Value.id: Value for Value in Values}
    if (
        len(Updates) != 2
        or len(
            {
                Value.expression.parameter_ids
                for Value in Values
                if Value.expression is not None
            }
        )
        != 2
    ):
        raise ValueError("Fusion Cut center dimensions reuse a parameter or driver")
    return Replace(
        Document,
        parameters=tuple(Updates.get(Value.id, Value) for Value in Document.parameters),
    )
