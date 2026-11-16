from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Authoring.MakeGeometry import MakeGeometry
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.mesh.SurfaceMesh import SurfaceMesh


# geometry without feature history needs valid neutral inputs independent of parameter presence
def BuildHistory(RecordKind: str, HasParams: bool) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("History boundary", "height", 20.0, ProfileKind="parameter")
    )
    Document = ReplaceData(
        Document, parameters=Document.parameters if HasParams else (), metadata={}
    )
    if RecordKind == "Mesh":
        return ReplaceData(
            Document,
            meshes=(
                SurfaceMesh(
                    "mesh:1",
                    "Triangle",
                    (
                        SpaceVector(0.0, 0.0, 0.0),
                        SpaceVector(1.0, 0.0, 0.0),
                        SpaceVector(0.0, 1.0, 0.0),
                    ),
                    ((0, 1, 2),),
                ),
            ),
        )
    Geometry, _ = MakeGeometry(DocumentSpec("Typed cylinder", "height", 20.0))
    return ReplaceData(
        Document,
        brep=ReplaceData(
            Geometry,
            bodies=tuple(
                ReplaceData(BodyValue, design_body_id="")
                for BodyValue in Geometry.bodies
            ),
        ),
    )
