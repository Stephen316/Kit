from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.BuildHistory import BuildHistory


# unrelated sketch history must not qualify local geometry without a body generator
def BuildSketchGeom(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Sketch-only history", "radius", 20.0, ProfileKind="circle")
    )
    Geometry = BuildHistory(RecordKind, False)
    return ReplaceData(
        Document, brep=Geometry.brep, meshes=Geometry.meshes, metadata={}
    )
