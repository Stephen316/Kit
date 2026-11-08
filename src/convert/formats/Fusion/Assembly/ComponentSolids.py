# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.ComponentScope import GetScopeRecords, IndexScope
from convert.formats.Fusion.Assembly.PackScope import PackAsmDef
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument, ComponentDoc
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody


# saved bodies belong to the definition document regardless of occurrence count
def AttachAsmSolids(
    Document: CadDocument,
    ComponentIds: dict[str, int],
    Inventory: dict[int, tuple[NativeBody, ...]],
    Solids: dict[int, tuple[tuple[DesignBody, ...], BrepModel]],
) -> CadDocument:
    if not Solids:
        return Document
    Assembly = Document.assembly
    if Assembly is None:
        raise ValueError("Fusion component solids require a verified assembly graph")
    Scopes = {Value.id: ComponentIds.get(Value.id) for Value in Assembly.definitions}
    NativeIds = tuple(Identity for Identity in Scopes.values() if Identity is not None)
    if (
        len(set(NativeIds)) != len(NativeIds)
        or Solids.keys() - set(NativeIds)
        or Solids.keys() - Inventory.keys()
    ):
        raise ValueError("Fusion assembly solid scopes do not match native definitions")
    Definitions = []
    Documents = list(Assembly.documents)
    Index = IndexScope(Document)
    Sketches = {Value.id: Value for Value in Document.sketches}
    for Definition in Assembly.definitions:
        ComponentId = Scopes[Definition.id]
        if ComponentId is not None and ComponentId in Solids:
            Solid = Solids[ComponentId]
            Definition, Scoped = PackAsmDef(
                Document,
                Definition,
                ComponentId,
                Definition.id == Assembly.root_definition_id,
                Inventory[ComponentId],
                Solid,
                GetScopeRecords(Solid[0], Index, Sketches),
            )
            if Definition.document_id:
                Documents.append(ComponentDoc(Definition.document_id, Scoped))
            else:
                Document = Scoped
        Definitions.append(Definition)
    Capabilities = Document.capabilities | {Capability.KBrep, Capability.KBodyStructure}
    if Documents:
        Capabilities |= {Capability.KComponentDocs}
    Result = Replace(
        Document,
        assembly=Replace(
            Assembly, definitions=tuple(Definitions), documents=tuple(Documents)
        ),
        capabilities=Capabilities,
    )
    Result.AssertValid()
    return Result
