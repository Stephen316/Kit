# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.Edits.AssemblyEdits import ReadAsmEdits
from convert.formats.Fusion.Assembly.ComponentSolids import AttachAsmSolids
from convert.formats.Fusion.Assembly.Solids.ScopedExtrudes import ReadScopedExts
from convert.formats.Fusion.Extrudes.SavedSolidSets import BuildSolidSets
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordDiagnostic import Diagnostic


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
