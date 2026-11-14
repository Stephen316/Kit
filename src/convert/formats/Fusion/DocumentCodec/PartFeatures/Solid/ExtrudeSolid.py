from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    MergeLabels,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionBool import KRegion
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionOp import (
    CheckStack,
    RegionOp,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import (
    IsTaperPair,
    SlabRoof,
)


def BoundLabel(
    Source: PrismSlab | None,
    Shaper: PrismSlab,
    Level: float,
    Covered: bool,
    Combine: str,
) -> FaceLabel:
    IsRoof = Source is not None and Level == Source.UpperCm
    if Combine == "cut":
        Tooling = None if Covered or Level != Shaper.LowerCm else Shaper.FloorLabel
    else:
        Tooling = Shaper.RoofLabel if Covered and Level == Shaper.UpperCm else None
    Origin = Source.RoofLabel if IsRoof and Source is not None else None
    if Origin is not None and Tooling is not None:
        return Origin if Combine == "cut" else MergeLabels(Origin, Tooling)
    Fallback = Source.RoofLabel if Source is not None else Shaper.RoofLabel
    return Origin or Tooling or Fallback


def FloorBound(
    Source: PrismSlab | None,
    Shaper: PrismSlab,
    Level: float,
    Covered: bool,
    Combine: str,
) -> FaceLabel:
    IsFloor = Source is not None and Level == Source.LowerCm
    if Combine == "cut":
        Tooling = None if Covered or Level != Shaper.UpperCm else Shaper.RoofLabel
    else:
        Tooling = Shaper.FloorLabel if Covered and Level == Shaper.LowerCm else None
    Origin = Source.FloorLabel if IsFloor and Source is not None else None
    if Origin is not None and Tooling is not None:
        return Origin if Combine == "cut" else MergeLabels(Origin, Tooling)
    Fallback = Source.FloorLabel if Source is not None else Shaper.FloorLabel
    return Origin or Tooling or Fallback


def SliceRoof(
    Source: PrismSlab | None,
    Shaper: PrismSlab,
    Bounds: tuple[float, float],
    Covered: bool,
) -> KRegion:
    if Source is not None and Source.RoofLoops:
        if Covered or Bounds != (Source.LowerCm, Source.UpperCm):
            raise ValueError("Fusion part tapered slabs cannot change again")
        return Source.RoofLoops
    if not Covered or not Shaper.RoofLoops:
        return ()
    if Source is None or Bounds != (Shaper.LowerCm, Shaper.UpperCm):
        raise ValueError("Fusion part tapers must cut within one body slab")
    return RegionOp(Source.Loops, Shaper.RoofLoops, "cut")


def TaperRoof(Loops: KRegion, RoofLoops: KRegion, Combine: str) -> KRegion:
    if not RoofLoops:
        return ()
    if Combine != "cut" or len(RoofLoops) != len(Loops):
        raise ValueError("Fusion part tapers only cut whole circles")
    if not all(IsTaperPair(Lower, Upper) for Lower, Upper in zip(Loops, RoofLoops)):
        raise ValueError("Fusion part tapers only cut whole circles")
    return RoofLoops


def SliceSlab(
    Solid: PrismSolid, Shaper: PrismSlab, Bounds: tuple[float, float], Combine: str
) -> PrismSlab | None:
    Lower, Upper = Bounds
    Source = next(
        (
            Value
            for Value in Solid.Slabs
            if Value.LowerCm <= Lower and Upper <= Value.UpperCm
        ),
        None,
    )
    Covered = Shaper.LowerCm <= Lower and Upper <= Shaper.UpperCm
    Loops = () if Source is None else Source.Loops
    if Covered:
        Loops = RegionOp(Loops, Shaper.Loops, Combine)
    elif Combine == "intersect":
        Loops = ()
    if not Loops:
        return None
    RoofLoops = TaperRoof(Loops, SliceRoof(Source, Shaper, Bounds, Covered), Combine)
    Floor = FloorBound(Source, Shaper, Lower, Covered, Combine)
    Ceiling = BoundLabel(Source, Shaper, Upper, Covered, Combine)
    return PrismSlab(Lower, Upper, Loops, Floor, Ceiling, RoofLoops)


def StackSlabs(Pieces: list[PrismSlab | None]) -> tuple[PrismSlab, ...]:
    Present = [Index for Index, Piece in enumerate(Pieces) if Piece is not None]
    Slabs: list[PrismSlab] = []
    for Piece in Pieces[Present[0] : Present[-1] + 1] if Present else ():
        if Piece is None:
            raise ValueError("Fusion part extrude would split the body")
        IsTapered = bool(Slabs) and bool(Slabs[-1].RoofLoops or Piece.RoofLoops)
        if Slabs and not IsTapered and Slabs[-1].Loops == Piece.Loops:
            Slabs[-1] = ReplaceValue(
                Slabs[-1], UpperCm=Piece.UpperCm, RoofLabel=Piece.RoofLabel
            )
            continue
        Slabs.append(Piece)
    if not Slabs:
        raise ValueError("Fusion part extrude removes the whole body")
    for Index, SlabValue in enumerate(Slabs):
        if sum(LoopArea(LoopValue) > 0 for LoopValue in SlabValue.Loops) != 1:
            raise ValueError("Fusion part extrude would create separate lumps")
        if Index:
            CheckStack(SlabRoof(Slabs[Index - 1]), SlabValue.Loops)
    return tuple(Slabs)


def ExtrudeSolid(
    Solid: PrismSolid, Shaper: PrismSlab, Combine: str, BodyLabel: FaceLabel | None
) -> PrismSolid:
    Levels = sorted(
        {Value.LowerCm for Value in Solid.Slabs}
        | {Value.UpperCm for Value in Solid.Slabs}
        | {Shaper.LowerCm, Shaper.UpperCm}
    )
    Pieces = [
        SliceSlab(Solid, Shaper, Bounds, Combine) for Bounds in zip(Levels, Levels[1:])
    ]
    Label = (
        Solid.BodyLabel
        if BodyLabel is None
        else MergeLabels(Solid.BodyLabel, BodyLabel)
    )
    return ReplaceValue(Solid, Slabs=StackSlabs(Pieces), BodyLabel=Label)
