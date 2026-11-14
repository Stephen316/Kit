from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)


def PickVertRoots(
    Links: tuple[CageLink, ...],
    VertexCount: int,
    Orientation: CageOrientation | None,
) -> dict[int, int]:
    Roots: dict[int, int] = {}
    if Orientation is None:
        for Index, LinkValue in enumerate(Links):
            _ = Roots.setdefault(LinkValue.VertexIndex, Index)
    else:
        if len(Orientation.Spokes) != VertexCount:
            raise ValueError("TSM vertex spokes must cover every vertex")
        Directed = {
            (LinkValue.VertexIndex, Links[LinkValue.NextLink].VertexIndex): Index
            for Index, LinkValue in enumerate(Links)
        }
        for Vertex, Target in enumerate(Orientation.Spokes):
            if (Vertex, Target) not in Directed:
                raise ValueError("TSM vertex spoke is not an outgoing edge")
            Roots[Vertex] = Directed[(Vertex, Target)]
    if set(Roots) != set(range(VertexCount)):
        raise ValueError("TSM authoring has an unused control vertex")
    return Roots
