from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData


def WriteCreases(Creases: CreaseData | None) -> tuple[str, ...]:
    if Creases is None:
        return ()
    Edges = " ".join(map(str, Creases.EdgeIndices))
    Vertices = " ".join(map(str, Creases.VertexIndices))
    return (
        "100edges" + (" " + Edges if Edges else ""),
        "100verts" + (" " + Vertices if Vertices else ""),
    )
