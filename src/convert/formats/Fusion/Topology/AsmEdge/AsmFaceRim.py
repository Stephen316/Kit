from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge


# a unique complete set of incident faces distinguishes vertices and edges with similar geometry
def ReadIncidence(
    Edges: dict[int, AsmPrismEdge],
) -> tuple[dict[frozenset[int], int], dict[frozenset[int], int]]:
    Vertices: dict[int, set[int]] = {}
    EdgeKeys: dict[frozenset[int], int] = {}
    for EdgeValue in Edges.values():
        if EdgeValue.Faces in EdgeKeys:
            raise ValueError("Fusion source prism edge incidence is ambiguous")
        EdgeKeys[EdgeValue.Faces] = EdgeValue.Identity
        for VertexId in EdgeValue.Vertices:
            Vertices.setdefault(VertexId, set()).update(EdgeValue.Faces)
    VertexKeys = {frozenset(Faces): VertexId for VertexId, Faces in Vertices.items()}
    if (
        len(VertexKeys) != 8
        or len(Vertices) != 8
        or any(len(Faces) != 3 for Faces in VertexKeys)
    ):
        raise ValueError("Fusion source prism vertex incidence is ambiguous")
    return EdgeKeys, VertexKeys
