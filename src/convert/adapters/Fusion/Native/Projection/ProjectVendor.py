from convert.adapters.Fusion.Native.Circular.ProjectCircular import ProjectCircular
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Projection.ProjectPrism import ProjectPrism
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordSource import CadSource


def ProjectVendor(Model: DocumentModel, Source: CadSource) -> CadDocument:
    if Model.Meshes or not (
        Model.Graphics is not None or Model.Snapshots or Model.Configurations
    ):
        raise ValueError(
            "Native-state version 2 requires the qualified auxiliary-bearing profile"
        )
    Graph = BuildGraph(Model)
    if Graph.ByClass("CircArc3D"):
        return ProjectCircular(Model, Source, Graph)
    return ProjectPrism(Model, Source, Graph)
