from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckCreases(Surface: TsplineSurface) -> None:
    if Surface.Creases is None:
        return
    CheckIndices(
        Surface.Creases.EdgeIndices, len(Surface.Topology.Edges), "creased edge"
    )
    CheckIndices(
        Surface.Creases.VertexIndices, len(Surface.Topology.Vertices), "creased vertex"
    )
