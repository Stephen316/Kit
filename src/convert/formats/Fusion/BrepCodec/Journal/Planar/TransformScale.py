from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    DotProduct,
)


def TransformScale(Value: TransformNode) -> float:
    Factor = (
        DotProduct(Value.ColumnX, CrossProduct(Value.ColumnY, Value.ColumnZ))
        * Value.ScaleFactor**3
    )
    if not IsFinite(Factor) or abs(Factor) <= 1e-15:
        raise ValueError("Fusion body transform is singular or oversized")
    return Factor
