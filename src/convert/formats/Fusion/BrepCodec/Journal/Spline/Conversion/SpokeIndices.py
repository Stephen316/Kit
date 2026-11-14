from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology

KSpokeNames = ("NORTH", "WEST", "SOUTH", "EAST")


def SpokeIndices(Topology: CageTopology) -> tuple[int, ...]:
    Spokes = [-1] * len(Topology.Links)
    for VertexIndex, Vertex in enumerate(Topology.Vertices):
        LinkIndex, Spoke, Turns = (
            Vertex.OriginLink,
            KSpokeNames.index(Vertex.Direction),
            0,
        )
        while True:
            LinkValue = Topology.Links[LinkIndex]
            if LinkValue.VertexIndex != VertexIndex or Spokes[LinkIndex] != -1:
                raise ValueError("Fusion grid conversion found a broken vertex fan")
            Spokes[LinkIndex] = Spoke
            Turns += 1 + LinkValue.ValenceOffset
            Spoke = (Spoke + 1 + LinkValue.ValenceOffset) % 4
            LinkIndex = Topology.Links[LinkValue.Previous].Opposite
            if LinkIndex == Vertex.OriginLink:
                break
        if Turns != 4:
            raise ValueError("Fusion grid conversion needs four spokes per vertex")
    if -1 in Spokes:
        raise ValueError("Fusion grid conversion found a link outside every fan")
    return tuple(Spokes)
