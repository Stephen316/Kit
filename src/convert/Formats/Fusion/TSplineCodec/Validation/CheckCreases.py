from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


# invalid creases input must fail here so control cage topology retains its native connectivity
def CheckCreases(Surface: TsplineSurface) -> None:
    if Surface.Creases is None:
        return
    CheckIndices(
        Surface.Creases.EdgeIndices, len(Surface.Topology.Edges), "creased edge"
    )
    CheckIndices(
        Surface.Creases.VertexIndices, len(Surface.Topology.Vertices), "creased vertex"
    )
