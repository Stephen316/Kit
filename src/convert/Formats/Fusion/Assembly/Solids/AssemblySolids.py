from dataclasses import replace as Replace

from convert.Formats.Fusion.Assembly.Edits.AssemblyEdits import ReadAsmEdits
from convert.Formats.Fusion.Assembly.ComponentSolids import AttachAsmSolids
from convert.Formats.Fusion.Assembly.Solids.ScopedExtrudes import ReadScopedExts
from convert.Formats.Fusion.Extrudes.SavedSolidSets import BuildSolidSets
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordDiagnostic import Diagnostic


# assembly body reconstruction requires the complete saved graph and native body inventory
def BuildAsmSolids(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    OwnerId: int,
    ComponentIds: dict[str, int],
    Inventory: dict[int, tuple[NativeBody, ...]],
) -> CadDocument:
    Assembly = Document.assembly
    if Assembly is None or not any(Inventory.values()):
        return Document
    try:
        if Inventory.keys() != set(ComponentIds.values()):
            raise ValueError("Fusion assembly body inventory is incomplete")
        Edits = ReadAsmEdits(BulkData, Spans, Assembly, Document.feature_timeline)
        OccurrenceIds = {
            int(Instance.provenance.native_id)
            for Instance in Assembly.instances
            if Instance.provenance is not None
        }
        if (
            len(Edits) != len(Assembly.instances)
            or set(Edits.values()) != OccurrenceIds
        ):
            raise ValueError("Fusion assembly occurrence history is incomplete")
        Owners = {
            SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
        }
        Scoped, Creators = ReadScopedExts(
            Document, Assembly, BulkData, Owners, OwnerId, Edits
        )
        Members = tuple(
            BodyValue for BodyList in Inventory.values() for BodyValue in BodyList
        )
        Solids = BuildSolidSets(Scoped, BulkData, Owners, Creators, Members)
        return AttachAsmSolids(Scoped, ComponentIds, Inventory, Solids)
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.assembly.body_unsupported", message=str(ErrorInfo)
                ),
            ),
        )
