from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
    StraightLink,
)

KRayMap = dict[int, int]


def TrackOrigins(Graph: CageGraph) -> frozenset[int]:
    Found: set[int] = set()
    for VertexIndex, FanLinks in enumerate(Graph.Fans):
        if Graph.Inside[VertexIndex] and len(FanLinks) != 4:
            Found.update(Entry for Entry in FanLinks if not Graph.Sharp[Entry])
    return frozenset(Found)


def DartOrigins(Graph: CageGraph) -> frozenset[int]:
    Found: set[int] = set()
    for LinkIndex, IsEdgeSharp in enumerate(Graph.Sharp):
        Onward = StraightLink(Graph, LinkIndex) if IsEdgeSharp else None
        if Onward is not None and not Graph.Sharp[Onward]:
            Found.add(Onward)
    if any(Graph.Links[Entry].Opposite in Found for Entry in Found):
        raise ValueError("Fusion Form face lines have no rule for a link joining darts")
    return frozenset(Found)


def LinkEnds(Graph: CageGraph, LinkIndex: int) -> tuple[int, int]:
    return Graph.Links[LinkIndex].VertexIndex, Graph.Heads[LinkIndex]


def MeetLinks(Graph: CageGraph, RayLinks: KRayMap) -> frozenset[int]:
    Moving = set(RayLinks.values())
    return frozenset(
        Origin
        for Origin, LinkIndex in RayLinks.items()
        if Graph.Links[LinkIndex].Opposite in Moving
    )


def ArriveRays(Graph: CageGraph, RayLinks: KRayMap) -> dict[int, list[int]]:
    Arrivals: dict[int, list[int]] = {}
    for Origin, LinkIndex in RayLinks.items():
        Arrivals.setdefault(Graph.Heads[LinkIndex], []).append(Origin)
    return Arrivals


def IsHeadOn(Graph: CageGraph, RayLinks: KRayMap, Arrived: list[int]) -> bool:
    Onward = {StraightLink(Graph, RayLinks[Origin]) for Origin in Arrived}
    return any(Graph.Links[RayLinks[Origin]].Opposite in Onward for Origin in Arrived)


def NextRays(Graph: CageGraph, RayLinks: KRayMap, Stops: frozenset[int]) -> KRayMap:
    Onward: KRayMap = {}
    for Vertex, Arrived in ArriveRays(Graph, RayLinks).items():
        if Vertex in Stops or IsHeadOn(Graph, RayLinks, Arrived):
            continue
        if len(Arrived) > 1:
            raise ValueError(
                "Fusion Form face lines tie where Fusion follows the grip geometry"
            )
        Origin = Arrived[0]
        NextLink = StraightLink(Graph, RayLinks[Origin])
        if NextLink is not None and Graph.Links[Origin].VertexIndex != Vertex:
            Onward[Origin] = NextLink
    return Onward


def StepRaysMut(
    Graph: CageGraph, RayLinks: KRayMap, Drawn: list[bool], Stops: set[int]
) -> KRayMap:
    Joined = MeetLinks(Graph, RayLinks)
    for LinkIndex in RayLinks.values():
        Drawn[LinkIndex] = Drawn[Graph.Links[LinkIndex].Opposite] = True
    Moving = {
        Origin: LinkIndex
        for Origin, LinkIndex in RayLinks.items()
        if Origin not in Joined
    }
    Onward = NextRays(Graph, Moving, frozenset(Stops))
    Stops.update(Graph.Heads[LinkIndex] for LinkIndex in Moving.values())
    return Onward


def DrawLines(Graph: CageGraph) -> tuple[bool, ...]:
    Drawn = list(Graph.Sharp)
    Stops = {
        Vertex
        for LinkIndex, IsEdgeSharp in enumerate(Graph.Sharp)
        if IsEdgeSharp
        for Vertex in LinkEnds(Graph, LinkIndex)
    }
    RayLinks = {Entry: Entry for Entry in sorted(TrackOrigins(Graph))}
    Waiting = {Entry: Entry for Entry in sorted(DartOrigins(Graph))}
    while RayLinks or Waiting:
        RayLinks = StepRaysMut(Graph, RayLinks, Drawn, Stops) | Waiting
        Waiting = {}
    return tuple(Drawn)
