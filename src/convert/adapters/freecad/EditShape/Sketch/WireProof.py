from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Sketch.SavedWireData import SavedWireData
from convert.adapters.freecad.EditShape.Sketch.WireEdge import ReadSavedEdge, SavedEdge
from convert.geometry.Opencascade import DecodeFailure, Reference, VertexData
from interchange.geometry.models.VectorSpace import SpaceVector


# each ordered wire consumes complete authored curve geometry and connects matching vertices
def ReadPathMut(
    DataValue: SavedWireData,
    WireRef: Reference,
    UsedEdges: set[int],
    DirectedLines: bool = False,
) -> tuple[SavedEdge, ...]:
    WireValue = DataValue.Records[WireRef.RecordA]
    if not WireValue.Children or WireRef.Orientation != "+":
        raise DecodeFailure("invalid saved sketch wire")
    Edges: list[SavedEdge] = []
    for EdgeRef in WireValue.Children:
        if DirectedLines and EdgeRef.Orientation != "+":
            raise DecodeFailure("saved sketch axis edge orientation changed")
        if EdgeRef.RecordA in UsedEdges:
            raise DecodeFailure("ambiguous saved sketch cache edge")
        UsedEdges.add(EdgeRef.RecordA)
        Edges.append(ReadSavedEdge(DataValue, EdgeRef))
    VertexPairs = [EdgeValue.VertexIds for EdgeValue in Edges]
    if any(
        Earlier[1] != Right[0] for Earlier, Right in zip(VertexPairs, VertexPairs[1:])
    ) or (WireValue.FlagBits[4] == "1") != (VertexPairs[0][0] == VertexPairs[-1][1]):
        raise DecodeFailure("saved sketch cache wire connectivity disagrees")
    return tuple(Edges)


# free vertices are an independent multiset even when coordinates coincide with curve endpoints
def CheckVertMut(
    DataValue: SavedWireData, VertexRef: Reference, Expected: list[SpaceVector]
) -> None:
    Record = DataValue.Records[VertexRef.RecordA]
    Vertex = Record.GeometryA
    if (
        Record.Children
        or not isinstance(Vertex, VertexData)
        or not 0 <= Vertex.Tolerance <= KPositionTolerance
    ):
        raise DecodeFailure("invalid saved sketch cache point")
    Match = next(
        (
            Index
            for Index, Value in enumerate(Expected)
            if IsNearPoint(Value, Vertex.Point)
        ),
        None,
    )
    if Match is None:
        raise DecodeFailure("saved sketch cache point disagrees with geometry")
    _ = Expected.pop(Match)


# all cache wires share one edge assignment while free vertices retain independent ownership
def ReadRootMut(
    DataValue: SavedWireData, Points: list[SpaceVector], DirectedLines: bool
) -> list[SavedEdge]:
    RootValue = DataValue.Records[DataValue.RootRef.RecordA]
    Children = (
        RootValue.Children if RootValue.KindValue == b"Co" else (DataValue.RootRef,)
    )
    if len({Child.RecordA for Child in Children}) != len(Children):
        raise DecodeFailure("duplicate saved sketch root reference")
    UsedEdges: set[int] = set()
    Edges: list[SavedEdge] = []
    for Child in Children:
        KindValue = DataValue.Records[Child.RecordA].KindValue
        if Child.Orientation != "+":
            raise DecodeFailure("invalid saved sketch root orientation")
        if KindValue == b"Wi":
            Edges.extend(ReadPathMut(DataValue, Child, UsedEdges, DirectedLines))
        elif KindValue == b"Ve":
            CheckVertMut(DataValue, Child, Points)
        else:
            raise DecodeFailure("unsupported saved sketch root record")
    return Edges
