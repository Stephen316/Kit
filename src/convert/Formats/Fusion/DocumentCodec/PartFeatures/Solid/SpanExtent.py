from math import floor as FloorValue, pi as KHalfTurn

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ArcPoint,
    SpanFinish,
    SpanStart,
)

# quarter turn must remain consistent across callers so body topology remains consistent with its modeling operation
KQuarterTurn = KHalfTurn / 2.0


# the span extent contract needs a shared interpretation so body topology remains consistent with its modeling operation
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
