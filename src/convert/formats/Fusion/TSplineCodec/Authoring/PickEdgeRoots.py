from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)


def PickEdgeRoots(
    Links: tuple[CageLink, ...], Orientation: CageOrientation | None
) -> dict[int, int]:
    Directed = {
        (LinkValue.VertexIndex, Links[LinkValue.NextLink].VertexIndex): Index
        for Index, LinkValue in enumerate(Links)
    }
    EdgeCount = len({LinkValue.EdgeIndex for LinkValue in Links})
    if Orientation is None:
        Origins = tuple(EdgePair for EdgePair in Directed if EdgePair[0] < EdgePair[1])
    else:
        Origins = Orientation.EdgeOrigins
    Roots: dict[int, int] = {}
    for EdgePair in Origins:
        if EdgePair not in Directed:
            raise ValueError("TSM edge origin is not a directed cage edge")
        LinkIndex = Directed[EdgePair]
        if Links[LinkIndex].EdgeIndex in Roots:
            raise ValueError("TSM edge origin repeats an edge")
        Roots[Links[LinkIndex].EdgeIndex] = LinkIndex
    if len(Roots) != EdgeCount:
        raise ValueError("TSM edge origins must cover every edge once")
    return Roots
