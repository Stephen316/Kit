from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly


# positive assembly coverage needs qualified child geometry with consistent body and mate references
def BuildTypedAsm() -> CadDocument:
    Document = BuildAssembly()
    assert Document.assembly is not None
    Assembly = Document.assembly
    PartValue = MakeFusionDoc(
        DocumentSpec(
            "Typed assembly part",
            "height",
            20.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    return ReplaceData(
        Document,
        assembly=ReplaceData(
            Assembly,
            definitions=tuple(
                (
                    ReplaceData(
                        Definition,
                        body_ids=tuple(BodyValue.id for BodyValue in PartValue.bodies),
                    )
                    if Definition.document_id == "document:part"
                    else Definition
                )
                for Definition in Assembly.definitions
            ),
            documents=(ReplaceData(Assembly.documents[0], document=PartValue),),
            mate_entities=tuple(
                (
                    ReplaceData(Entity, source_entity_id="plane")
                    if Entity.id == "mate-entity:part"
                    else Entity
                )
                for Entity in Assembly.mate_entities
            ),
        ),
    )
