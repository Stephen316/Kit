from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyUses(Layout: PolyLayout) -> tuple[CoedgeNode, ...]:
    Links = tuple(
        (FaceIndex, LocalIndex, Start, RingValue[(LocalIndex + 1) % len(RingValue)])
        for FaceIndex, RingValue in enumerate(Layout.FaceLoops)
        for LocalIndex, Start in enumerate(RingValue)
    )
    Results: list[CoedgeNode] = []
    for FaceIndex, LocalIndex, Start, Finish in Links:
        Partners = tuple(
            Other
            for Other, (_, _, First, FinishRef) in enumerate(Links)
            if First == Finish and FinishRef == Start
        )
        if len(Partners) != 1:
            raise ValueError("Fusion polyhedron edge requires exactly one opposite use")
        EdgeIndex = Layout.Edges.index((min(Start, Finish), max(Start, Finish)))
        Count = len(Layout.FaceLoops[FaceIndex])
        FirstUse = Layout.CoedgeBase + Layout.LoopStarts[FaceIndex]
        Results.append(
            CoedgeNode(
                EntityPrefix(-1, -1),
                FirstUse + (LocalIndex + 1) % Count,
                FirstUse + (LocalIndex - 1) % Count,
                Layout.CoedgeBase + Partners[0],
                Layout.EdgeBase + EdgeIndex,
                Start > Finish,
                Layout.LoopBase + FaceIndex,
            )
        )
    return tuple(Results)
