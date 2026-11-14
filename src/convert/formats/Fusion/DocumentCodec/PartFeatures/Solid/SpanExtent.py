from math import floor as FloorValue, pi as KHalfTurn

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ArcPoint,
    SpanFinish,
    SpanStart,
)

KQuarterTurn = KHalfTurn / 2.0


def SpanExtent(Value: KPlaneSpan) -> list[tuple[float, float]]:
    Points = [SpanStart(Value), SpanFinish(Value)]
    if not isinstance(Value, ArcSpan):
        return Points
    Lower = min(Value.StartAngle, Value.StartAngle + Value.SweepAngle)
    Upper = max(Value.StartAngle, Value.StartAngle + Value.SweepAngle)
    Quarter = FloorValue(Lower / KQuarterTurn) + 1
    while Quarter * KQuarterTurn < Upper:
        Points.append(ArcPoint(Value, Quarter * KQuarterTurn))
        Quarter += 1
    return Points
