from math import isfinite as IsFinite
from struct import pack as PackValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData


def PackVertices(Value: VertexData | None, Width: int, Format: str) -> bytes | None:
    if Value is None:
        return None
    if type(Value.Values) is not tuple or any(
        type(Vertex) is not tuple or len(Vertex) != Width for Vertex in Value.Values
    ):
        raise ValueError("Invalid graphics vertex dimensions")
    Numbers = tuple(Number for Vertex in Value.Values for Number in Vertex)
    if any(type(Number) is not float or not IsFinite(Number) for Number in Numbers):
        raise ValueError("Expected finite floating graphics vertices")
    return PackValue(Format, *Numbers)
