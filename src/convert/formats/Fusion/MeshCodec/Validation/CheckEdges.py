from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


def CheckEdges(Value: ParaMesh) -> None:
    TriangleEdges: set[tuple[int, int]] = set()
    for Offset in range(0, len(Value.Corners), 3):
        First, Second, Third = Value.Corners[Offset : Offset + 3]
        for Start, Finish in ((First, Second), (Second, Third), (Third, First)):
            TriangleEdges.add((min(Start, Finish), max(Start, Finish)))
    Present: set[tuple[int, int]] = set()
    for EdgeValue in Value.Edges:
        PairValue = EdgeValue.First, EdgeValue.Second
        if type(EdgeValue.First) is not int or type(EdgeValue.Second) is not int:
            raise ValueError("Fusion mesh feature edge requires integer endpoints")
        if (
            EdgeValue.First >= EdgeValue.Second
            or PairValue in Present
            or PairValue not in TriangleEdges
        ):
            raise ValueError(
                "Fusion mesh feature edge is duplicate or outside triangle topology"
            )
        Present.add(PairValue)
