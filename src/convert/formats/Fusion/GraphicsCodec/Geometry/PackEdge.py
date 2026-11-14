from math import isfinite as IsFinite
from struct import pack as PackValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge


def PackEdge(Value: EnhancedEdge | None, Format: str) -> bytes | None:
    if Value is None:
        return None
    Columns = (Value.Points, Value.Normals)
    if any(
        type(Column) is not tuple
        or any(type(Vertex) is not tuple or len(Vertex) != 3 for Vertex in Column)
        for Column in Columns
    ) or len(Value.Points) != len(Value.Normals):
        raise ValueError("Invalid graphics enhanced edge dimensions")
    Numbers = tuple(
        Number
        for Point, Normal in zip(Value.Points, Value.Normals, strict=True)
        for Number in (*Point, *Normal)
    )
    if any(type(Number) is not float or not IsFinite(Number) for Number in Numbers):
        raise ValueError("Expected finite floating graphics edge vertices")
    return PackValue(Format, *Numbers)
