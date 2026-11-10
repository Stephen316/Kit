# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.AssemblyBodies import AttachBodyList
from convert.formats.Fusion.Assembly.Solids.AssemblySolids import BuildAsmSolids
from convert.formats.Fusion.Extrudes.ExtrudeBody import ProjectExtBody
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    KBodyInventoryKey,
    LinkBodyRecords,
)
from convert.formats.Fusion.Topology.BodyInventory import ReadBodyInventory
from convert.formats.Fusion.Topology.BodyScope import FindBodyScope
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordDiagnostic import Diagnostic


# assembly definitions and explicit history views keep their own saved body membership
def ProjectBodyList(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
) -> CadDocument:
    Assembly = Document.assembly
    ComponentIds = (
        {
            Definition.id: int(Definition.provenance.native_id)
            for Definition in Assembly.definitions
            if Definition.provenance is not None
        }
        if Assembly is not None
        else {}
    )
    ScopeId = None
    try:
        if Assembly is None:
            ScopeId = FindBodyScope(BulkData, Spans, History)
            if ScopeId is None:
                return Document
        Scope = frozenset(ComponentIds.values() if ScopeId is None else (ScopeId,))
        Inventory, Issues = ReadBodyInventory(BulkData, Spans, Scope)
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.body.inventory_unsupported", message=str(ErrorInfo)
                ),
            ),
        )
    Diagnostics = Document.diagnostics + tuple(
        Diagnostic(
            code="fusion.body.inventory_unsupported",
            message=Message,
            entity_id=f"fusion-component-{ComponentId}",
        )
        for ComponentId, Message in sorted(Issues.items())
    )
    if Assembly is not None:
        Updated = Replace(
            Document,
            assembly=AttachBodyList(Assembly, ComponentIds, Inventory),
            diagnostics=Diagnostics,
        )
        return BuildAsmSolids(
            Updated, BulkData, Spans, History.OwnerId, ComponentIds, Inventory
        )
    if ScopeId is None or ScopeId not in Inventory:
        return Replace(Document, diagnostics=Diagnostics)
    Members = Inventory[ScopeId]
    Document = ProjectExtBody(
        Replace(Document, diagnostics=Diagnostics), BulkData, Spans, Members
    )
    Bodies, LinkedIds = LinkBodyRecords(Document.bodies, Members)
    return Replace(
        Document,
        bodies=Bodies,
        metadata=FreezeMapping(
            {
                **Document.metadata,
                KBodyInventoryKey: GetBodyEvidence(ScopeId, Members, LinkedIds),
            }
        ),
    )
