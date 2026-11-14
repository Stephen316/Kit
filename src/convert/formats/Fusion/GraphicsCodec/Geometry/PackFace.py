from math import isfinite as IsFinite
from struct import pack as PackValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace


def PackFace(
    Value: EnhancedFace | None, FloatFormat: str, IndexFormat: str
) -> bytes | None:
    if Value is None:
        return None
    Columns = ((Value.Points, 3), (Value.Normals, 3), (Value.Coords, 2))
    if any(
        type(Column) is not tuple
        or len(Column) != len(Value.Points)
        or any(type(Vertex) is not tuple or len(Vertex) != Width for Vertex in Column)
        for Column, Width in Columns
    ):
        raise ValueError("Invalid graphics enhanced face dimensions")
    Numbers = tuple(
        Number
        for Point, Normal, Coord in zip(
            Value.Points, Value.Normals, Value.Coords, strict=True
        )
        for Number in (*Point, *Normal, *Coord)
    )
    if any(type(Number) is not float or not IsFinite(Number) for Number in Numbers):
        raise ValueError("Expected finite floating graphics face vertices")
    if type(Value.Indices) is not tuple or any(
        type(Number) is not int for Number in Value.Indices
    ):
        raise ValueError("Expected integer graphics face indices")
    return PackValue(FloatFormat, *Numbers) + PackValue(IndexFormat, *Value.Indices)
