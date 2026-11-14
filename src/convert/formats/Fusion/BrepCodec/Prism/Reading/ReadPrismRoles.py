from convert.formats.Fusion.BrepCodec.Prism.Reading.OrderCorners import OrderCorners
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)


def ReadPrismRoles(Graph: PrismGraph) -> PrismRoles:
    Corners = {
        Identity: Index for Index, Identity in enumerate(OrderCorners(Graph.Points))
    }
    EdgeKeys = {frozenset(Value): Index for Index, Value in enumerate(KEdgeCorners)}
    FaceKeys = {frozenset(Value): Index for Index, Value in enumerate(KFaceCorners)}
    try:
        Edges = {
            Identity: EdgeKeys[frozenset(Corners[Vertex] for Vertex in Value.Vertices)]
            for Identity, Value in Graph.Edges.items()
        }
        Faces = {
            Identity: FaceKeys[
                frozenset(
                    Corners[Vertex]
                    for Value in RingValue
                    for Vertex in Graph.Edges[Value.EdgeId].Vertices
                )
            ]
            for Identity, RingValue in Graph.Rings.items()
        }
    except KeyError as ErrorInfo:
        raise ValueError(
            "Prism topology does not match rectangular roles"
        ) from ErrorInfo
    if set(Edges.values()) != set(range(12)) or set(Faces.values()) != set(range(6)):
        raise ValueError("Prism topology aliases geometric roles")
    return PrismRoles(Corners, Faces, Edges)
