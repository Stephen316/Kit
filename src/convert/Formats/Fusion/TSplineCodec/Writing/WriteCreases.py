from convert.Formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData


# the creases operation needs a consistent construction rule so control cage topology retains its native connectivity
def WriteCreases(Creases: CreaseData | None) -> tuple[str, ...]:
    if Creases is None:
        return ()
    Edges = " ".join(map(str, Creases.EdgeIndices))
    Vertices = " ".join(map(str, Creases.VertexIndices))
    return (
        "100edges" + (" " + Edges if Edges else ""),
        "100verts" + (" " + Vertices if Vertices else ""),
    )
