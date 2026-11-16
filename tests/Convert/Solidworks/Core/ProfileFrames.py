from tests.Convert.Solidworks.Core.MarkerFrame import KMarkerSize, MarkerFrame

# a closed rectangle anchors the expected four edge traversal
KRectPoints = ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0))

# a distinct polygon checks that adjacent contours retain separate identities
KPolyPoints = ((0.0, 0.0), (2.0, 0.0), (3.0, 1.0), (2.0, 2.0), (0.0, 2.0), (-1.0, 1.0))


# independent frames give traversal assertions expected owned edges and rejected headers
def ProfileFrames(
    BaseIndex: int, InsertAt: int, Count: int, Headers: bool
) -> tuple[bytes, set[int], set[int], set[int]]:
    Frames = [MarkerFrame(0, PointValue) for PointValue in KRectPoints] * Count
    PolyStart = BaseIndex + Count * 4
    PolyOffsets = {InsertAt + (len(Frames) + Index) * KMarkerSize for Index in range(6)}
    Frames.extend(MarkerFrame(0, PointValue) for PointValue in KPolyPoints)
    HeaderOffsets: set[int] = set()
    RectOffsets: set[int] = set()
    for Index in range(Count):
        VertexBase = BaseIndex + Index * 4
        if Headers:
            HeaderOffsets.add(InsertAt + len(Frames) * KMarkerSize)
            Frames.append(MarkerFrame(0, Endpoints=(VertexBase, VertexBase + 2)))
        for EdgeIndex in range(4):
            RectOffsets.add(InsertAt + len(Frames) * KMarkerSize)
            Frames.append(
                MarkerFrame(
                    1,
                    Endpoints=(
                        VertexBase + EdgeIndex,
                        VertexBase + (EdgeIndex + 1) % 4,
                    ),
                )
            )
    for Index in range(6):
        PolyOffsets.add(InsertAt + len(Frames) * KMarkerSize)
        Frames.append(
            MarkerFrame(1, Endpoints=(PolyStart + Index, PolyStart + (Index + 1) % 6))
        )
    return b"".join(Frames), HeaderOffsets, RectOffsets, PolyOffsets
