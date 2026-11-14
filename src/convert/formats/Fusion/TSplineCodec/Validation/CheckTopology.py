from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckLinks import CheckLinks
from convert.formats.Fusion.TSplineCodec.Validation.CheckFaces import CheckFaces
from convert.formats.Fusion.TSplineCodec.Validation.CheckEdges import CheckEdges
from convert.formats.Fusion.TSplineCodec.Validation.CheckVertices import CheckVertices


def CheckTopology(Topology: CageTopology) -> None:
    Counts = (
        len(Topology.Faces),
        len(Topology.Edges),
        len(Topology.Vertices),
        len(Topology.Links),
    )
    if any(not 0 < Count <= 1000000 for Count in Counts) or len(
        Topology.Links
    ) != 2 * len(Topology.Edges):
        raise ValueError("Invalid TSM topology allocation")
    CheckLinks(Topology)
    CheckFaces(Topology)
    CheckEdges(Topology)
    CheckVertices(Topology)
