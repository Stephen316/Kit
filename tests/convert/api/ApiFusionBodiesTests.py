from typing import cast as CastValue
from json import loads as LoadJson

from tests.convert.FusionRead import OpenResearch as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# namespaced evidence preserves membership without asserting geometry reconstruction
KInventory = "fusion.body_inventory"


# named interleaved assembly bodies belong to native definitions rather than instances
@KRequiresCodec
def CheckBodyOwner() -> None:
    Folder = KStudyPath / "namedbodies-3c7c11fc2924"
    Archive = Folder / "namedbodies.f3d"
    Oracle = LoadJson((Folder / "ground_truth.json").read_text(encoding="utf-8"))
    Document = OpenDocument(Archive, StrictMode=False, IncludeBrep=False)
    Assembly = Document.assembly
    assert Assembly is not None
    Names = {
        (Definition.name, Member["stored_name"])
        for Definition in Assembly.definitions
        for Member in CastValue(
            dict[str, tuple[dict[str, object], ...]], Definition.attributes[KInventory]
        )["members"]
    }
    assert Names == {
        (RowValue["component_name"], RowValue["name"]) for RowValue in Oracle["bodies"]
    }
    RootValue = Assembly.definition(Assembly.root_definition_id)
    assert tuple(
        Member["object_id"]
        for Member in CastValue(
            dict[str, tuple[dict[str, object], ...]], RootValue.attributes[KInventory]
        )["members"]
    ) == (401, 543)
    Child = next(
        Definition
        for Definition in Assembly.definitions
        if Definition.name == "Module A"
    )
    ChildDoc = OpenDocument(
        Archive,
        StrictMode=False,
        Configuration=str(Child.attributes["fusion.history_id"]),
    )
    assert ChildDoc.assembly is None
    (ChildMember,) = CastValue(
        dict[str, tuple[dict[str, object], ...]], ChildDoc.metadata[KInventory]
    )["members"]
    (LinkedMember,) = CastValue(
        dict[str, tuple[dict[str, object], ...]], Child.attributes[KInventory]
    )["members"]
    assert ChildMember["object_id"] == LinkedMember["object_id"] == 480
    assert ChildMember["design_body_id"] is None
    assert LinkedMember["design_body_id"] in Child.body_ids
    assert len(Document.bodies) == 2 and Document.brep is None
    assert {
        Capability.KBodyStructure,
        Capability.KComponentDocs,
    } <= Document.capabilities
    assert CadDocument.from_json(Document.to_json()) == Document


# retained source records must not reappear as members after body removal
@KRequiresCodec
def CheckRemoved() -> None:
    Archive = KStudyPath / "removecontrasts-9c5f83456a0e" / "root_body.f3d"
    Document = OpenDocument(Archive, StrictMode=False)
    (Member,) = CastValue(
        dict[str, tuple[dict[str, object], ...]], Document.metadata[KInventory]
    )["members"]
    assert Member["object_id"] == 354
    assert Member["stored_name"] == "RemoveSurvivorBody"
    assert Member["design_body_id"] is None


# projected solids and saved membership continue to share the original neutral ids
@KRequiresCodec
def CheckBodyLink() -> None:
    Archive = KStudyPath / "analytic-86a12b291d0a" / "analytic.f3d"
    Document = OpenDocument(Archive, StrictMode=False)
    assert Document.brep is not None and len(Document.bodies) == 3
    assert Capability.KBodyStructure in Document.capabilities
    Members = {
        Member["object_id"]: Member
        for Member in CastValue(
            dict[str, tuple[dict[str, object], ...]], Document.metadata[KInventory]
        )["members"]
    }
    for BodyValue in Document.bodies:
        assert BodyValue.provenance is not None
        Member = Members[int(BodyValue.provenance.native_id)]
        assert Member["design_body_id"] == BodyValue.id
        assert (
            Member["collection_id"]
            == BodyValue.attributes["fusion.native_body_collection_id"]
        )
        assert (
            BodyValue.attributes["fusion.component_object_id"]
            == CastValue(dict[str, object], Document.metadata[KInventory])[
                "component_id"
            ]
        )
    assert CadDocument.from_json(Document.to_json()) == Document
