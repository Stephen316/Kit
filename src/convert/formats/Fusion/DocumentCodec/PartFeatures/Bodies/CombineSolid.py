from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    MoveSlab,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed

KStayPlace = ((0.0, 0.0), 0.0, False)


def CombineSolid(
    Target: PrismSolid,
    Tools: tuple[PrismSolid, ...],
    Feature: CombineSpec,
    Operation: int,
) -> PrismSolid:
    if IsSealed(Target):
        raise ValueError("Fusion combines take bodies that are not tapered or swept")
    Result = Target
    for ToolSolid in Tools:
        if len(ToolSolid.Slabs) != 1 or IsSealed(ToolSolid):
            raise ValueError("Fusion combine tools must be single straight slabs")
        Shaper = MoveSlab(ToolSolid.Slabs[0], KStayPlace, (Operation,))
        Joined = ToolSolid.BodyLabel if Feature.Operation == "join" else None
        Result = ExtrudeSolid(Result, Shaper, Feature.Operation, Joined)
    return ReplaceValue(Result, Ordinal=Target.Ordinal)
