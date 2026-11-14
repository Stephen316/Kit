from math import tan as Tangent, pi as KPiValue

from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def RotaryShape(
    Context: ExtrudeContext, Shape: CircleShape, History: HistoryModel | FrustumHistory
) -> FrustumBody:
    Height = NumberValue(Context.Along.Fields["value"]) * 10
    Angle = NumberValue(Context.Taper.Fields["value"])
    if not -KPiValue / 2 < Angle < KPiValue / 2:
        raise ValueError(
            "Native circular taper is outside the positive-radius frustum domain"
        )
    Model = FrustumBody(
        Shape.Geometry.radius,
        Shape.Geometry.radius + Height * Tangent(Angle),
        Height,
        (Shape.Geometry.center.x, Shape.Geometry.center.y, 0.0),
    )
    if isinstance(History, HistoryModel):
        if Angle != 0:
            raise ValueError("Native taper parameter requires conical history geometry")
        Radii = (History.Model.Radius, History.Model.Radius)
    else:
        Radii = (History.Model.BottomRadius, History.Model.TopRadius)
    SameNumbers(
        (*Radii, History.Model.Height, *History.Model.BasePoint),
        (Model.BottomRadius, Model.TopRadius, Model.Height, *Model.BasePoint),
    )
    return Model
