from dataclasses import replace as ReplaceData

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.BuildHistory import BuildHistory
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly


# assembly coverage must include local mesh representations that have no embedded child history
def BuildHistoryAsm() -> CadDocument:
    Document = BuildAssembly()
    assert Document.assembly is not None
    Definitions = tuple(
        (
            ReplaceData(Definition, document_id="", body_ids=(), mesh_ids=("mesh:1",))
            if Definition.document_id
            else Definition
        )
        for Definition in Document.assembly.definitions
    )
    return ReplaceData(
        Document,
        meshes=BuildHistory("Mesh", False).meshes,
        assembly=ReplaceData(Document.assembly, definitions=Definitions, documents=()),
    )
