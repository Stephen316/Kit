from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import PointKey
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanStart,
)

# the vertex key shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KVertexKey = tuple[float, float, float]


# the space key contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SpaceKey(Point: KSpaceVector) -> KVertexKey:
    return (*PointKey((Point[0], Point[1])), Point[2])


# the use ends contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def UseEnds(UseValue: ShapeUse) -> tuple[KVertexKey, KVertexKey]:
    EdgeValue = UseValue.Edge
    if isinstance(EdgeValue, LevelEdge):
        Start = PointKey(SpanStart(EdgeValue.Span))
        Finish = PointKey(SpanFinish(EdgeValue.Span))
        Former = (*Start, EdgeValue.LevelCm)
        Latter = (*Finish, EdgeValue.LevelCm)
    elif isinstance(EdgeValue, FreeEdge):
        Former, Latter = SpaceKey(EdgeValue.StartCm), SpaceKey(EdgeValue.FinishCm)
    else:
        Point = PointKey(EdgeValue.PointCm)
        Summit = PointKey(EdgeValue.TopCm or EdgeValue.PointCm)
        Former, Latter = (*Point, EdgeValue.LowerCm), (*Summit, EdgeValue.UpperCm)
    return (Former, Latter) if UseValue.Forward else (Latter, Former)


# next use needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def NextUse(
    EndPairs: list[tuple[KVertexKey, KVertexKey]],
    IsUsed: list[bool],
    Vertex: KVertexKey,
) -> int:
    for Index, PairValue in enumerate(EndPairs):
        if not IsUsed[Index] and PairValue[0] == Vertex:
            return Index
    raise ValueError("Fusion part face boundary is not a closed loop")


# the chain uses contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def ChainUses(UseList: list[ShapeUse]) -> tuple[tuple[ShapeUse, ...], ...]:
    EndPairs = [UseEnds(UseValue) for UseValue in UseList]
    IsUsed = [False] * len(UseList)
    Loops: list[tuple[ShapeUse, ...]] = []
    for First in range(len(UseList)):
        if IsUsed[First]:
            continue
        Circuit: list[ShapeUse] = []
        Current = First
        while True:
            IsUsed[Current] = True
            Circuit.append(UseList[Current])
            if EndPairs[Current][1] == EndPairs[First][0]:
                break
            Current = NextUse(EndPairs, IsUsed, EndPairs[Current][1])
        Loops.append(tuple(Circuit))
    return tuple(Loops)
