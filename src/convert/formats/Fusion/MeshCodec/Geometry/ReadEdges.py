from convert.formats.Fusion.MeshCodec.Model.FeatureEdge import FeatureEdge
from convert.formats.Fusion.MeshCodec.Streams.ReadTerminal import ReadTerminal


def ReadEdges(Payload: bytes) -> tuple[FeatureEdge, ...]:
    Values = ReadTerminal(Payload)
    if len(Values) % 2:
        raise ValueError("Invalid Fusion mesh feature-edge allocation")
    return tuple(
        FeatureEdge(Values[Index], Values[Index + 1])
        for Index in range(0, len(Values), 2)
    )
