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


# the slab roof contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SlabRoof(SlabValue: PrismSlab) -> tuple[KPlaneLoop, ...]:
    return SlabValue.RoofLoops or SlabValue.Loops


# the slab pairs contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SlabPairs(SlabValue: PrismSlab) -> tuple[tuple[KPlaneLoop, KPlaneLoop], ...]:
    return tuple(zip(SlabValue.Loops, SlabRoof(SlabValue), strict=True))


# the tapered decision must stay consistent so body topology remains consistent with its modeling operation
def IsTapered(Solid: PrismSolid) -> bool:
    return any(SlabValue.RoofLoops for SlabValue in Solid.Slabs)


# the sealed decision must stay consistent so body topology remains consistent with its modeling operation
def IsSealed(Solid: PrismSolid) -> bool:
    return Solid.Sealed or IsTapered(Solid) or bool(Solid.Rounds)


# the same span decision must stay consistent so body topology remains consistent with its modeling operation
def IsSameSpan(First: KPlaneSpan, Second: KPlaneSpan) -> bool:
    return type(First) is type(Second) and (
        ReplaceValue(First, Label=Second.Label) == Second
    )


# the same ring decision must stay consistent so body topology remains consistent with its modeling operation
def IsSameRing(First: KPlaneLoop, Second: KPlaneLoop) -> bool:
    return len(First) == len(Second) and all(
        IsSameSpan(Value, Other) for Value, Other in zip(First, Second)
    )


# the taper pair decision must stay consistent so body topology remains consistent with its modeling operation
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
