from dataclasses import replace as ReplaceData

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.document.Models.DocumentModel import CadDocument
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly


# qualification coverage must inspect embedded child documents with consistent assembly references
def WrapDocument(Document: CadDocument) -> CadDocument:
    Assembly = BuildAssembly()
    assert Assembly.assembly is not None
    Definitions = tuple(
        (
            ReplaceData(
                Definition,
                kind=(
                    ComponentKind.KAssembly
                    if Document.assembly
                    else ComponentKind.KPart
                ),
                body_ids=tuple(BodyValue.id for BodyValue in Document.bodies),
            )
            if Definition.document_id
            else Definition
        )
        for Definition in Assembly.assembly.definitions
    )
    Nested = ReplaceData(Assembly.assembly.documents[0], document=Document)
    return ReplaceData(
        Assembly,
        assembly=ReplaceData(
            Assembly.assembly, definitions=Definitions, documents=(Nested,)
        ),
    )
