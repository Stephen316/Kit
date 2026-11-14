from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink


def MakeLinks(
    Faces: tuple[tuple[int, ...], ...], VertexCount: int
) -> tuple[CageLink, ...]:
    Directed: dict[tuple[int, int], int] = {}
    EdgeIds: dict[tuple[int, int], int] = {}
    Records: list[tuple[int, int, int, int, int]] = []
    for FaceIndex, Vertices in enumerate(Faces):
        if (
            len(Vertices) != 4
            or len(set(Vertices)) != 4
            or any(
                type(Index) is not int or not 0 <= Index < VertexCount
                for Index in Vertices
            )
        ):
            raise ValueError("TSM authoring requires distinct valid quad vertices")
        Offset = len(Records)
        for Corner, VertexIndex in enumerate(Vertices):
            Following = Vertices[(Corner + 1) % 4]
            if (VertexIndex, Following) in Directed:
                raise ValueError("TSM authoring has a repeated directed edge")
            Directed[(VertexIndex, Following)] = len(Records)
            EdgeKey = (min(VertexIndex, Following), max(VertexIndex, Following))
            EdgeIndex = EdgeIds.setdefault(EdgeKey, len(EdgeIds))
            Records.append(
                (
                    Offset + (Corner - 1) % 4,
                    Offset + (Corner + 1) % 4,
                    VertexIndex,
                    FaceIndex,
                    EdgeIndex,
                )
            )
    if any((Second, First) not in Directed for First, Second in Directed):
        raise ValueError("TSM authoring requires a closed oriented cage")
    return tuple(
        CageLink(
            Previous,
            Following,
            Directed[(Records[Following][2], VertexIndex)],
            VertexIndex,
            FaceIndex,
            EdgeIndex,
        )
        for Previous, Following, VertexIndex, FaceIndex, EdgeIndex in Records
    )
