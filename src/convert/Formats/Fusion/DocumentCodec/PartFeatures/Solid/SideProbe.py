from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ArcPoint,
    SpanFinish,
    SpanHeading,
    SpanStart,
)

# probe offset must remain consistent across callers so body topology remains consistent with its modeling operation
KProbeOffset = 1e-5


# the side probe contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SideProbe(
    Value: KPlaneSpan,
) -> tuple[tuple[float, float], tuple[float, float]]:
    if isinstance(Value, ArcSpan):
        Middle = ArcPoint(Value, Value.StartAngle + Value.SweepAngle / 2.0)
        Halved = ArcSpan(
            Value.CenterCm,
            Value.RadiusCm,
            Value.StartAngle + Value.SweepAngle / 2.0,
            Value.SweepAngle / 2.0,
            Value.Label,
        )
        HeadX, HeadY = SpanHeading(Halved, False)
    else:
        Start, Finish = SpanStart(Value), SpanFinish(Value)
        Middle = ((Start[0] + Finish[0]) / 2.0, (Start[1] + Finish[1]) / 2.0)
        HeadX, HeadY = SpanHeading(Value, False)
    return (
        (Middle[0] - HeadY * KProbeOffset, Middle[1] + HeadX * KProbeOffset),
        (Middle[0] + HeadY * KProbeOffset, Middle[1] - HeadX * KProbeOffset),
    )
