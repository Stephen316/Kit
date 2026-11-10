# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.ComponentDoc import MakeAsmDoc
from convert.formats.Fusion.Assembly.ComponentScope import KScopeRecord
from convert.formats.Fusion.Assembly.ScopeCheck import CheckScope
from convert.formats.Fusion.Assembly.SolidMembership import GetSolidMembers
from convert.formats.Fusion.Topology.BodyEvidence import KBodyInventoryKey
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody


# the root retains its full timeline while linked definitions use detached local scopes
def PackAsmDef(
    Document: CadDocument,
    Definition: ComponentDef,
    ComponentId: int,
    IsRoot: bool,
    Members: tuple[NativeBody, ...],
    Solid: tuple[tuple[DesignBody, ...], BrepModel],
    Records: tuple[KScopeRecord, ...],
) -> tuple[ComponentDef, CadDocument]:
    if Definition.document_id or Definition.body_ids:
        raise ValueError(f"Fusion component {ComponentId} already has body links")
    Bodies, Model = Solid
    Bodies, Evidence = GetSolidMembers(ComponentId, Members, Bodies, Model)
    CheckScope(Records, ComponentId)
    if IsRoot:
        if Document.bodies or Document.brep is not None:
            raise ValueError("Fusion assembly root already has solid geometry")
        DocumentId = ""
        Scoped = Replace(Document, bodies=Bodies, brep=Model)
    else:
        DocumentId = f"fusion-component-document-{ComponentId}"
        Scoped = MakeAsmDoc(Document, Records, Bodies, Model, Evidence)
    return (
        Replace(
            Definition,
            document_id=DocumentId,
            body_ids=tuple(Value.id for Value in Bodies),
            attributes=FreezeMapping(
                {**Definition.attributes, KBodyInventoryKey: Evidence}
            ),
        ),
        Scoped,
    )
