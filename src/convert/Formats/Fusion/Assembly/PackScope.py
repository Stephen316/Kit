from dataclasses import replace as Replace

from convert.Formats.Fusion.Assembly.ComponentDoc import MakeAsmDoc
from convert.Formats.Fusion.Assembly.ComponentScope import KScopeRecord
from convert.Formats.Fusion.Assembly.ScopeCheck import CheckScope
from convert.Formats.Fusion.Assembly.SolidMembership import GetSolidMembers
from convert.Formats.Fusion.Topology.BodyEvidence import KBodyInventoryKey
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureBody import DesignBody


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
