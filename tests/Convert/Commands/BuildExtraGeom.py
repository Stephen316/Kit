from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordProvenance import Provenance
from tests.Convert.Commands.BuildHistory import BuildHistory


# unowned geometry must remain unqualified even beside valid history or persuasive metadata
def BuildExtraGeom(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec(
            "Typed geometry owner",
            "height",
            20.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    if RecordKind == "UnlinkedBrep":
        assert Document.brep is not None
        return ReplaceData(
            Document,
            brep=ReplaceData(
                Document.brep,
                bodies=tuple(
                    ReplaceData(BodyValue, design_body_id="")
                    for BodyValue in Document.brep.bodies
                ),
            ),
            metadata={},
        )
    MeshValue = BuildHistory("Mesh", False).meshes[0]
    if RecordKind == "TaggedMesh":
        MeshValue = ReplaceData(
            MeshValue,
            attributes={
                "feature_id": "extrude",
                "design_body_id": "body",
                "parametric": True,
            },
            provenance=Provenance(
                "fixture",
                "extrude",
                attributes={"feature_id": "extrude", "design_body_id": "body"},
            ),
        )
    return ReplaceData(Document, meshes=(MeshValue,), metadata={})
