from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    ShiftLabel,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed


# the shift loops contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def ShiftLoops(
    Loops: tuple[KPlaneLoop, ...], Extra: tuple[int, ...]
) -> tuple[KPlaneLoop, ...]:
    return tuple(
        tuple(
            ReplaceValue(Value, Label=ShiftLabel(Value.Label, Extra))
            for Value in LoopValue
        )
        for LoopValue in Loops
    )


# the shift slab contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def ShiftSlab(Shaper: PrismSlab, Extra: tuple[int, ...]) -> PrismSlab:
    return ReplaceValue(
        Shaper,
        Loops=ShiftLoops(Shaper.Loops, Extra),
        FloorLabel=ShiftLabel(Shaper.FloorLabel, Extra),
        RoofLabel=ShiftLabel(Shaper.RoofLabel, Extra),
        RoofLoops=ShiftLoops(Shaper.RoofLoops, Extra),
    )


# paste solid needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def PasteSolid(Source: PrismSolid, Operation: int, Ordinal: int) -> PrismSolid:
    if IsSealed(Source):
        raise ValueError("Fusion body pastes take bodies that are not tapered or swept")
    Extra = (Operation,)
    return PrismSolid(
        tuple(ShiftSlab(SlabValue, Extra) for SlabValue in Source.Slabs),
        FaceLabel(str(Operation), (), 1),
        tuple(
            (ShiftLabel(Label, Extra), CurveTag)
            for Label, CurveTag in Source.SketchCurves
        ),
        tuple(
            (ShiftLabel(WallLabel, Extra), Level, RimLabel)
            for WallLabel, Level, RimLabel in Source.EdgeTags
        ),
        tuple((ShiftLabel(Label, Extra), Index) for Label, Index in Source.Tracks),
        Ordinal,
    )
