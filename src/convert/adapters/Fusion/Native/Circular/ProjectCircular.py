from convert.adapters.Fusion.Native.Circular.ProjectRound import ProjectRound
from convert.adapters.Fusion.Native.Circular.ProjectDisk import ProjectDisk
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordSource import CadSource


def ProjectCircular(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    if Graph.ByClass("DcExtrudeFeature"):
        return ProjectRound(Model, Source, Graph)
    return ProjectDisk(Model, Source, Graph)
