from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.BuildHistory import BuildHistory
from tests.convert.Commands.Sketch.BuildSketches import BuildSketches
from tests.convert.Commands.WrapDocument import WrapDocument


# metadata child scenarios need valid documents that bypass the ordinary assembly walk
def BuildSidecar(RecordKind: str, IsNested: bool) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Sidecar parent", "height", 20.0, ProfileKind="parameter")
    )
    Child = (
        BuildHistory("Mesh", False)
        if RecordKind == "Mesh"
        else BuildSketches("Empty") if RecordKind == "Sketch" else Document
    )
    Child.AssertValid()
    Document = ReplaceData(
        Document,
        metadata={
            "freecad": {
                "external_documents": [
                    {"file": "child.FCStd", "document": Child.to_dict()}
                ]
            }
        },
    )
    return WrapDocument(Document) if IsNested else Document
