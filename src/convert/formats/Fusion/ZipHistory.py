from collections.abc import Callable
from dataclasses import replace as Replace

from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.HistoryProjection import ProjectHistory
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.ZipParameters import ReadBulkParams
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# shared indexing connects native feature references with validated numeric ownership
def ReadZipHistory(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[tuple[HistoryPart, ...], tuple[Parameter, ...], tuple[Diagnostic, ...]]:
    BulkData, Spans = ReadDesignZip(DataValue, InflateZstd)
    return ReadBulkHistory(BulkData, Spans)


# document projection shares one archive index across history and geometry readers
def ReadBulkHistory(
    BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> tuple[tuple[HistoryPart, ...], tuple[Parameter, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Params, ParamIssues = ReadBulkParams(BulkData, Spans)
    ParamIds: dict[int, list[str]] = {}
    for ParamValue in Params:
        OwnerId = ParamValue.attributes.get("fusion.owner_object_id")
        if isinstance(OwnerId, int):
            ParamIds.setdefault(OwnerId, []).append(ParamValue.id)
    Parts: list[HistoryPart] = []
    Diagnostics = list(ParamIssues)
    for SpanValue in Owners.values():
        if SpanValue.ClassGuid != KHistoryGuid:
            continue
        try:
            Parts.append(ProjectHistory(BulkData, SpanValue, Owners, ParamIds))
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.history.unsupported",
                    message=str(ErrorInfo),
                    provenance=ParamOrigin(SpanValue),
                )
            )
    StepOwners: dict[str, list[str]] = {}
    for PartValue in Parts:
        for StepValue in PartValue.Steps:
            for ParamId in StepValue.parameter_ids:
                StepOwners.setdefault(ParamId, []).append(StepValue.id)
    Linked: list[Parameter] = []
    for ParamValue in Params:
        Candidates = StepOwners.get(ParamValue.id, [])
        Linked.append(
            Replace(ParamValue, owner_id=Candidates[0])
            if len(Candidates) == 1
            else ParamValue
        )
    return tuple(Parts), tuple(Linked), tuple(Diagnostics)
