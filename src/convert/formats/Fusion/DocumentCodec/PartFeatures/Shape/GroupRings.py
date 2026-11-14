from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    LoopArea,
    LoopPolygon,
    WindNumber,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ReverseSpan,
    SpanStart,
)

KRing = tuple[ShapeUse, ...]


def RingLoop(RingValue: KRing) -> KPlaneLoop:
    Spans: list[KPlaneSpan] = []
    for UseValue in RingValue:
        if not isinstance(UseValue.Edge, LevelEdge):
            raise ValueError("Fusion part cap rings hold only level edges")
        SpanValue = UseValue.Edge.Span
        Spans.append(SpanValue if UseValue.Forward else ReverseSpan(SpanValue))
    return tuple(Spans)


def GroupRings(Rings: tuple[KRing, ...], Upward: bool) -> list[tuple[KRing, ...]]:
    Loops = [RingLoop(RingValue) for RingValue in Rings]
    Outer = [
        Index
        for Index, LoopValue in enumerate(Loops)
        if (LoopArea(LoopValue) > 0) == Upward
    ]
    Groups: dict[int, list[KRing]] = {Index: [Rings[Index]] for Index in Outer}
    for Index, LoopValue in enumerate(Loops):
        if Index in Outer:
            continue
        Point = SpanStart(LoopValue[0])
        Hosts = [
            HostIndex
            for HostIndex in Outer
            if WindNumber(LoopPolygon(Loops[HostIndex]), Point) != 0
        ]
        if not Hosts:
            raise ValueError("Fusion part cap boundary has no enclosing outer loop")
        Smallest = min(Hosts, key=lambda HostIndex: abs(LoopArea(Loops[HostIndex])))
        Groups[Smallest].append(Rings[Index])
    return [tuple(Members) for Members in Groups.values()]
