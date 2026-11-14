from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def OrientState(
    Surface: TsplineSurface,
) -> tuple[
    frozenset[tuple[tuple[float, float, float], ...]],
    frozenset[tuple[tuple[float, float, float], tuple[float, float, float]]],
    frozenset[tuple[tuple[float, float, float], tuple[float, float, float]]],
]:
    Links = Surface.Topology.Links
    Points = tuple(
        (Value.CoordX, Value.CoordY, Value.CoordZ) for Value in Surface.Grips
    )

    def Endpoints(
        LinkIndex: int,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        LinkValue = Links[LinkIndex]
        return (
            Points[LinkValue.VertexIndex],
            Points[Links[LinkValue.NextLink].VertexIndex],
        )

    FaceRings: set[tuple[tuple[float, float, float], ...]] = set()
    for FaceValue in Surface.Topology.Faces:
        Corners = [Points[Links[FaceValue.OriginLink].VertexIndex]]
        Current = Links[FaceValue.OriginLink].NextLink
        while Current != FaceValue.OriginLink:
            Corners.append(Points[Links[Current].VertexIndex])
            Current = Links[Current].NextLink
        FaceRings.add(tuple(Corners))
    Spokes = frozenset(
        Endpoints(Value.OriginLink) for Value in Surface.Topology.Vertices
    )
    Origins = frozenset(Endpoints(Value.OriginLink) for Value in Surface.Topology.Edges)
    return frozenset(FaceRings), Spokes, Origins
