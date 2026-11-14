from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import (
    ArcRange,
    OffsetCircle,
    OffsetJoint,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanHeading,
)


def InsetSpan(
    Value: KPlaneSpan,
    Start: tuple[float, float],
    Finish: tuple[float, float],
    AmountCm: float,
    Label: FaceLabel,
) -> KPlaneSpan:
    if isinstance(Value, LineSpan):
        HeadX, HeadY = SpanHeading(Value, False)
        if (Finish[0] - Start[0]) * HeadX + (Finish[1] - Start[1]) * HeadY <= 1e-9:
            raise ValueError("Fusion part shell thickness consumes a profile side")
        return LineSpan(Finish, Start, Label)
    Circle = OffsetCircle(Value, AmountCm)
    if Circle is None:
        raise ValueError("Fusion part shell arcs need an offset circle")
    Begin, Delta = ArcRange(Circle[0], Start, Finish, Value.SweepAngle)
    return ArcSpan(Circle[0], Circle[1], Begin + Delta, -Delta, Label)


def InsetLoop(LoopValue: KPlaneLoop, AmountCm: float, Operation: int) -> KPlaneLoop:
    Joints = [
        OffsetJoint(Value, LoopValue[(Index + 1) % len(LoopValue)], AmountCm)
        for Index, Value in enumerate(LoopValue)
    ]
    Spans = [
        InsetSpan(
            Value,
            Joints[Index - 1],
            Joints[Index],
            AmountCm,
            FaceLabel(Value.Label.PrimaryId, Value.Label.OperationIds + (Operation,)),
        )
        for Index, Value in enumerate(LoopValue)
    ]
    return tuple(reversed(Spans))
