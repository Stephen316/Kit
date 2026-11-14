from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    IsLoopClosed,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanStart


def CanonLoop(LoopValue: KPlaneLoop) -> KPlaneLoop:
    if not LoopValue or not IsLoopClosed(LoopValue):
        raise ValueError("Fusion part profile loops must be closed and non-empty")
    KeyList = [
        (round(SpanStart(Value)[0], 9), round(SpanStart(Value)[1], 9))
        for Value in LoopValue
    ]
    First = min(range(len(LoopValue)), key=lambda Index: KeyList[Index])
    return LoopValue[First:] + LoopValue[:First]
