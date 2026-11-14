from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.OffsetLoop import (
    KOffsetLimit,
    OffsetIndex,
    ShiftLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)

KLabelPairs = tuple[tuple[FaceLabel, FaceLabel], ...]


def MarkLabel(Label: FaceLabel, Operation: int) -> FaceLabel:
    if Label.Merged:
        raise ValueError("Fusion offset faces require single-tag faces")
    return ReplaceValue(Label, OperationIds=Label.OperationIds + (-Operation,))


def MarkLoop(LoopValue: KPlaneLoop, Marks: dict[int, int]) -> KPlaneLoop:
    return tuple(
        (
            ReplaceValue(Value, Label=MarkLabel(Value.Label, Marks[Index]))
            if Index in Marks
            else Value
        )
        for Index, Value in enumerate(LoopValue)
    )


def LoopPairs(
    Sources: tuple[KPlaneLoop, ...], Marked: tuple[KPlaneLoop, ...]
) -> KLabelPairs:
    return tuple(
        (Source.Label, Value.Label)
        for SourceLoop, MarkedLoop in zip(Sources, Marked, strict=True)
        for Source, Value in zip(SourceLoop, MarkedLoop, strict=True)
    )


def RaiseRoof(
    SlabValue: PrismSlab, DistanceCm: float, Operation: int
) -> tuple[PrismSlab, KLabelPairs]:
    Upper = SlabValue.UpperCm + DistanceCm
    if Upper <= SlabValue.LowerCm + KOffsetLimit:
        raise ValueError("Fusion offset distance collapses the body")
    Loops = tuple(
        MarkLoop(LoopValue, dict.fromkeys(range(len(LoopValue)), Operation + 1))
        for LoopValue in SlabValue.Loops
    )
    Ceiling = MarkLabel(SlabValue.RoofLabel, Operation)
    Pairs = LoopPairs(SlabValue.Loops, Loops) + ((SlabValue.RoofLabel, Ceiling),)
    Floor = SlabValue.FloorLabel
    return PrismSlab(SlabValue.LowerCm, Upper, Loops, Floor, Ceiling), Pairs


def ShiftSide(
    SlabValue: PrismSlab, Feature: OffsetSpec, Operation: int
) -> tuple[PrismSlab, KLabelPairs]:
    if len(SlabValue.Loops) != 1 or Feature.SideMm is None:
        raise ValueError("Fusion side offsets require one profile loop")
    LoopValue = SlabValue.Loops[0]
    Index = OffsetIndex(LoopValue, (Feature.SideMm[0] / 10.0, Feature.SideMm[1] / 10.0))
    Shifted = ShiftLoop(LoopValue, Index, Feature.DistanceMm / 10.0)
    Count = len(LoopValue)
    Marks = {(Index - 1) % Count: Operation + 1, (Index + 1) % Count: Operation + 1}
    Marks[Index] = Operation
    Marked = MarkLoop(Shifted, Marks)
    CapLabels = (SlabValue.FloorLabel, SlabValue.RoofLabel)
    Floor, Ceiling = (MarkLabel(Label, Operation + 1) for Label in CapLabels)
    Pairs = LoopPairs((LoopValue,), (Marked,))
    Pairs += ((CapLabels[0], Floor), (CapLabels[1], Ceiling))
    Lower, Upper = SlabValue.LowerCm, SlabValue.UpperCm
    return PrismSlab(Lower, Upper, (CanonLoop(Marked),), Floor, Ceiling), Pairs


def LabelMap(Pairs: KLabelPairs) -> dict[FaceLabel, FaceLabel]:
    Renamed: dict[FaceLabel, FaceLabel] = {}
    for OldLabel, NewLabel in Pairs:
        if Renamed.setdefault(OldLabel, NewLabel) != NewLabel:
            raise ValueError("Fusion offset faces require distinctly tagged faces")
    return {
        OldLabel: NewLabel
        for OldLabel, NewLabel in Renamed.items()
        if OldLabel != NewLabel
    }


def OffsetSolid(Solid: PrismSolid, Feature: OffsetSpec, Operation: int) -> PrismSolid:
    if len(Solid.Slabs) != 1 or Solid.EdgeTags or Solid.Slabs[0].RoofLoops:
        raise ValueError("Fusion offset faces require one prism slab without circles")
    if Feature.SideMm is None:
        DistanceCm = Feature.DistanceMm / 10.0
        Moved, Pairs = RaiseRoof(Solid.Slabs[0], DistanceCm, Operation)
    else:
        Moved, Pairs = ShiftSide(Solid.Slabs[0], Feature, Operation)
    Renamed = LabelMap(Pairs)
    Curves = tuple(
        (Renamed[Label], Curve)
        for Label, Curve in Solid.SketchCurves
        if Label in Renamed
    )
    Tracks = tuple((Renamed.get(Label, Label), Index) for Label, Index in Solid.Tracks)
    return ReplaceValue(
        Solid,
        Slabs=(Moved,),
        SketchCurves=Solid.SketchCurves + Curves,
        Tracks=Tracks,
    )
