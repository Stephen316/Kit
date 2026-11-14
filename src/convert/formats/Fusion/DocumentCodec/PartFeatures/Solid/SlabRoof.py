from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)


def SlabRoof(SlabValue: PrismSlab) -> tuple[KPlaneLoop, ...]:
    return SlabValue.RoofLoops or SlabValue.Loops


def SlabPairs(SlabValue: PrismSlab) -> tuple[tuple[KPlaneLoop, KPlaneLoop], ...]:
    return tuple(zip(SlabValue.Loops, SlabRoof(SlabValue), strict=True))


def IsTapered(Solid: PrismSolid) -> bool:
    return any(SlabValue.RoofLoops for SlabValue in Solid.Slabs)


def IsSealed(Solid: PrismSolid) -> bool:
    return Solid.Sealed or IsTapered(Solid) or bool(Solid.Rounds)


def IsSameSpan(First: KPlaneSpan, Second: KPlaneSpan) -> bool:
    return type(First) is type(Second) and (
        ReplaceValue(First, Label=Second.Label) == Second
    )


def IsSameRing(First: KPlaneLoop, Second: KPlaneLoop) -> bool:
    return len(First) == len(Second) and all(
        IsSameSpan(Value, Other) for Value, Other in zip(First, Second)
    )


def IsTaperPair(Lower: KPlaneLoop, Upper: KPlaneLoop) -> bool:
    if Lower == Upper:
        return True
    if len(Lower) != 1 or len(Upper) != 1:
        return False
    Bottom, Summit = Lower[0], Upper[0]
    if not isinstance(Bottom, ArcSpan) or not isinstance(Summit, ArcSpan):
        return False
    Circles = IsFullCircle(Bottom) and IsFullCircle(Summit)
    return (
        Circles and Bottom.CenterCm == Summit.CenterCm and Bottom.Label == Summit.Label
    )
