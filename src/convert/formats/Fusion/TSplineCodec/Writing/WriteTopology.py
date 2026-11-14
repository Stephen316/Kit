from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


def WriteTopology(Topology: CageTopology) -> tuple[str, ...]:
    Faces = tuple(
        f"f {Value.OriginLink} {int(Value.IsHidden)}" for Value in Topology.Faces
    )
    Edges = tuple(
        f"e {Value.OriginLink} {NumberText(Value.KnotInterval)}"
        for Value in Topology.Edges
    )
    Vertices = tuple(
        f"v {Value.OriginLink} {Value.Direction}" for Value in Topology.Vertices
    )
    Links = tuple(
        "l "
        + " ".join(
            map(
                str,
                (
                    Value.Previous,
                    Value.NextLink,
                    Value.Opposite,
                    Value.VertexIndex,
                    Value.FaceIndex,
                    Value.EdgeIndex,
                    Value.ValenceOffset,
                ),
            )
        )
        for Value in Topology.Links
    )
    Conditions = tuple(
        f"ec {Value.EdgeIndex} {NumberText(Value.EndValue)}"
        for Value in Topology.EndConditions
    )
    return Faces + Edges + Vertices + Links + Conditions
