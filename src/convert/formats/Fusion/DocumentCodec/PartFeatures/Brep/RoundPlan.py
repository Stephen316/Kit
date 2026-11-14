from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundChain import (
    ChainSeed,
    KUsePlace,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundFrame import (
    EdgeSense,
    SideNormal,
    UseEnds,
    WallOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
    SubVector,
    VectorLength,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace

KTangentLimit = 1e-9


@MakeDataClass(frozen=True, slots=True)
class ChainLink:
    UseIndex: int
    WallIndex: int
    Start: KSpaceVector
    Finish: KSpaceVector


@MakeDataClass(frozen=True, slots=True)
class RoundPlan:
    CapIndex: int
    LoopIndex: int
    Links: tuple[ChainLink, ...]
    Numbers: tuple[int, ...]
    Closed: bool
    Sense: float
    Mitres: tuple[bool, ...]


def LinkAt(
    Shape: ShapeBody, Users: dict[KShapeEdge, list[KUsePlace]], SeedValue: ChainSeed
) -> ChainLink | None:
    UseValue = Shape.Faces[SeedValue.CapIndex].Loops[SeedValue.LoopIndex][
        SeedValue.UseIndex
    ]
    if not isinstance(UseValue.Edge, LevelEdge):
        return None
    WallIndex = WallOf(Shape, Users, UseValue.Edge, SeedValue.CapIndex)
    Start, Finish = UseEnds(UseValue)
    return ChainLink(SeedValue.UseIndex, WallIndex, Start, Finish)


def IsTangent(Shape: ShapeBody, Before: ChainLink, After: ChainLink) -> bool:
    First, Second = Shape.Faces[Before.WallIndex], Shape.Faces[After.WallIndex]
    if not isinstance(First, WallFace) or not isinstance(Second, WallFace):
        return False
    GapVector = SubVector(
        SideNormal(First, Before.Finish), SideNormal(Second, After.Start)
    )
    return VectorLength(GapVector) < KTangentLimit


def StepLink(
    Shape: ShapeBody,
    Users: dict[KShapeEdge, list[KUsePlace]],
    SeedValue: ChainSeed,
    Offset: int,
) -> ChainLink | None:
    Count = len(Shape.Faces[SeedValue.CapIndex].Loops[SeedValue.LoopIndex])
    Index = (SeedValue.UseIndex + Offset) % Count
    return LinkAt(
        Shape, Users, ChainSeed(SeedValue.CapIndex, SeedValue.LoopIndex, Index)
    )


def WalkLinks(
    Shape: ShapeBody,
    Users: dict[KShapeEdge, list[KUsePlace]],
    SeedValue: ChainSeed,
    Direction: int,
) -> list[ChainLink]:
    Count = len(Shape.Faces[SeedValue.CapIndex].Loops[SeedValue.LoopIndex])
    Found: list[ChainLink] = []
    Current = LinkAt(Shape, Users, SeedValue)
    for Offset in range(1, Count):
        Following = StepLink(Shape, Users, SeedValue, Offset * Direction)
        if Current is None or Following is None:
            break
        LinkPair = (Current, Following) if Direction > 0 else (Following, Current)
        if not IsTangent(Shape, *LinkPair):
            break
        Found.append(Following)
        Current = Following
    return Found


def PlanRound(
    Shape: ShapeBody, Users: dict[KShapeEdge, list[KUsePlace]], SeedValue: ChainSeed
) -> RoundPlan:
    SeedLink = LinkAt(Shape, Users, SeedValue)
    if SeedLink is None:
        raise ValueError("Fusion edge rounds need a horizontal body edge")
    Count = len(Shape.Faces[SeedValue.CapIndex].Loops[SeedValue.LoopIndex])
    Ahead = WalkLinks(Shape, Users, SeedValue, 1)
    Closed = len(Ahead) == Count - 1 and (
        Count == 1 or IsTangent(Shape, Ahead[-1], SeedLink)
    )
    Behind = [] if Closed else WalkLinks(Shape, Users, SeedValue, -1)
    Links = (*reversed(Behind), SeedLink, *Ahead)
    Numbers = (*range(len(Links) - 1, len(Ahead), -1), *range(len(Ahead) + 1))
    CapValue = Shape.Faces[SeedValue.CapIndex]
    WallValue = Shape.Faces[SeedLink.WallIndex]
    if not isinstance(CapValue, CapFace) or not isinstance(WallValue, WallFace):
        raise ValueError("Fusion edge rounds need a cap and a side face")
    Sense = EdgeSense(CapValue, WallValue)
    Mitres = (False,) * (len(Links) + (0 if Closed else 1))
    return RoundPlan(
        SeedValue.CapIndex, SeedValue.LoopIndex, Links, Numbers, Closed, Sense, Mitres
    )
