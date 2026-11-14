from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue


def ReadVectorMut(Cursor: MetaCursor) -> VectorValue:
    XCoord, YCoord, ZCoord = (
        float(Number) for Number in UnpackValue("<ddd", Cursor.TakeBytes(24))
    )
    if not all(IsFinite(Number) for Number in (XCoord, YCoord, ZCoord)):
        raise ValueError("Nonfinite Fusion feature vector")
    return VectorValue(XCoord, YCoord, ZCoord)
