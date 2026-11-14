from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionBool import (
    KRegion,
    RegionBool,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSameRing
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanCross import SpanCross


def RegionOp(Loops: KRegion, Shaper: KRegion, Combine: str) -> KRegion:
    if not Loops:
        return Shaper if Combine == "join" else ()
    return RegionBool(Loops, Shaper, Combine)


def IsApart(First: KPlaneLoop, Second: KPlaneLoop) -> bool:
    return not any(SpanCross(Former, Latter) for Former in First for Latter in Second)


def CheckStack(Lower: KRegion, Upper: KRegion) -> None:
    for Below in Lower:
        for Above in Upper:
            if Below in Upper or Above in Lower or IsSameRing(Below, Above):
                continue
            if not IsApart(Below, Above):
                raise ValueError("Fusion part slab boundaries cross between levels")
