from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology

KSpokeSteps = ((0, 1), (-1, 0), (0, -1), (1, 0))


def PlaceVertices(
    Topology: CageTopology, Spokes: tuple[int, ...]
) -> tuple[tuple[int, int], ...]:
    if not Topology.Faces:
        raise ValueError("Fusion grid conversion needs a face")
    Origin = Topology.Faces[0].OriginLink
    if Spokes[Origin] != 3:
        raise ValueError("Fusion grid conversion needs an eastward first face")
    VertexFans: dict[int, list[int]] = {}
    for LinkIndex, LinkValue in enumerate(Topology.Links):
        if Spokes[LinkValue.Opposite] != (Spokes[LinkIndex] + 2) % 4:
            raise ValueError("Fusion grid conversion found a twisted edge")
        VertexFans.setdefault(LinkValue.VertexIndex, []).append(LinkIndex)
    Start = Topology.Links[Origin].VertexIndex
    Places: dict[int, tuple[int, int]] = {Start: (0, 0)}
    Pending = [Start]
    while Pending:
        Vertex = Pending.pop()
        for LinkIndex in VertexFans[Vertex]:
            LinkValue = Topology.Links[LinkIndex]
            StepU, StepV = KSpokeSteps[Spokes[LinkIndex]]
            Place = (Places[Vertex][0] + StepU, Places[Vertex][1] + StepV)
            Target = Topology.Links[LinkValue.Opposite].VertexIndex
            if Target not in Places:
                Places[Target] = Place
                Pending.append(Target)
            elif Places[Target] != Place:
                raise ValueError("Fusion grid conversion found an irregular cage")
    if len(Places) != len(Topology.Vertices):
        raise ValueError("Fusion grid conversion needs a connected cage")
    return tuple(Places[Index] for Index in range(len(Topology.Vertices)))
