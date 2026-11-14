from tests.convert.solidworks.core.MarkerFrame import KMarkerSize, MarkerFrame

KRectPoints = ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0))
KPolyPoints = ((0.0, 0.0), (2.0, 0.0), (3.0, 1.0), (2.0, 2.0), (0.0, 2.0), (-1.0, 1.0))


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
