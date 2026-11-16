from convert.Formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
    StraightLink,
)

# the ray map shape must stay shared so capped spline reconstruction uses one contract for compatible values
KRayMap = dict[int, int]


# the track origins contract needs a shared interpretation so cap boundaries remain connected to the surrounding surface
def TrackOrigins(Graph: CageGraph) -> frozenset[int]:
    Found: set[int] = set()
    for VertexIndex, FanLinks in enumerate(Graph.Fans):
        if Graph.Inside[VertexIndex] and len(FanLinks) != 4:
            Found.update(Entry for Entry in FanLinks if not Graph.Sharp[Entry])
    return frozenset(Found)


# dart origins needs an explicit validity boundary so cap boundaries remain connected to the surrounding surface
def DartOrigins(Graph: CageGraph) -> frozenset[int]:
    Found: set[int] = set()
    for LinkIndex, IsEdgeSharp in enumerate(Graph.Sharp):
        Onward = StraightLink(Graph, LinkIndex) if IsEdgeSharp else None
        if Onward is not None and not Graph.Sharp[Onward]:
            Found.add(Onward)
    if any(Graph.Links[Entry].Opposite in Found for Entry in Found):
        raise ValueError("Fusion Form face lines have no rule for a link joining darts")
    return frozenset(Found)


# link ends must resolve unambiguously so cap boundaries remain connected to the surrounding surface
def LinkEnds(Graph: CageGraph, LinkIndex: int) -> tuple[int, int]:
    return Graph.Links[LinkIndex].VertexIndex, Graph.Heads[LinkIndex]


# the meet links contract needs a shared interpretation so cap boundaries remain connected to the surrounding surface
def MeetLinks(Graph: CageGraph, RayLinks: KRayMap) -> frozenset[int]:
    Moving = set(RayLinks.values())
    return frozenset(
        Origin
        for Origin, LinkIndex in RayLinks.items()
        if Graph.Links[LinkIndex].Opposite in Moving
    )


# the arrive rays contract needs a shared interpretation so cap boundaries remain connected to the surrounding surface
def ArriveRays(Graph: CageGraph, RayLinks: KRayMap) -> dict[int, list[int]]:
    Arrivals: dict[int, list[int]] = {}
    for Origin, LinkIndex in RayLinks.items():
        Arrivals.setdefault(Graph.Heads[LinkIndex], []).append(Origin)
    return Arrivals


# the head on decision must stay consistent so cap boundaries remain connected to the surrounding surface
def IsHeadOn(Graph: CageGraph, RayLinks: KRayMap, Arrived: list[int]) -> bool:
    Onward = {StraightLink(Graph, RayLinks[Origin]) for Origin in Arrived}
    return any(Graph.Links[RayLinks[Origin]].Opposite in Onward for Origin in Arrived)


# next rays needs an explicit validity boundary so cap boundaries remain connected to the surrounding surface
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


# the step rays contract needs a shared interpretation so cap boundaries remain connected to the surrounding surface
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


# the draw lines contract needs a shared interpretation so cap boundaries remain connected to the surrounding surface
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
