from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue


# the vector operation needs a consistent construction rule so native records retain their segment ownership and schema
def EmitVector(Value: KFieldValue) -> bytes:
    if not isinstance(Value, VectorValue):
        raise ValueError("Fusion feature vector requires typed coordinates")
    Coords = (Value.XCoord, Value.YCoord, Value.ZCoord)
    if not all(type(Number) in (int, float) and IsFinite(Number) for Number in Coords):
        raise ValueError("Invalid Fusion feature vector coordinate")
    return PackValue("<ddd", *Coords)
