from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue


# the vector operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadVectorMut(Cursor: MetaCursor) -> VectorValue:
    XCoord, YCoord, ZCoord = (
        float(Number) for Number in UnpackValue("<ddd", Cursor.TakeBytes(24))
    )
    if not all(IsFinite(Number) for Number in (XCoord, YCoord, ZCoord)):
        raise ValueError("Nonfinite Fusion feature vector")
    return VectorValue(XCoord, YCoord, ZCoord)
