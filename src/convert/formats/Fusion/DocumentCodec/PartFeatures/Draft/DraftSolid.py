from dataclasses import replace as ReplaceValue
from math import radians as Radians, tan as Tangent

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.OffsetLoop import (
    IsSimple,
    KeptPiece,
    KOffsetLimit,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import (
    OffsetJoint,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def DraftLoops(
    LoopValue: KPlaneLoop, SpreadCm: float, Operation: int
) -> tuple[KPlaneLoop, KPlaneLoop]:
    Count = len(LoopValue)
    Joints = [
        OffsetJoint(LoopValue[Index], LoopValue[(Index + 1) % Count], -SpreadCm)
        for Index in range(Count)
    ]
    Labels: list[FaceLabel] = []
    for Value in LoopValue:
        if Value.Label.Merged:
            raise ValueError("Fusion drafts require single-tag side faces")
        Marked = Value.Label.OperationIds + (-Operation,)
        Labels.append(ReplaceValue(Value.Label, OperationIds=Marked))
    Bottom = tuple(
        ReplaceValue(Value, Label=Label) for Value, Label in zip(LoopValue, Labels)
    )
    Summit = tuple(
        KeptPiece(Bottom[Index], Joints[Index - 1], Joints[Index])
        for Index in range(Count)
    )
    if LoopArea(Summit) <= KOffsetLimit or not IsSimple(Summit):
        raise ValueError("Fusion draft angle folds the top profile")
    return Bottom, Summit


def DraftSolid(Solid: PrismSolid, Feature: DraftSpec, Operation: int) -> PrismSolid:
    if len(Solid.Slabs) != 1 or Solid.EdgeTags or Solid.Slabs[0].RoofLoops:
        raise ValueError("Fusion drafts require one prism slab without circles")
    SlabValue = Solid.Slabs[0]
    if len(SlabValue.Loops) != 1 or not all(
        isinstance(Value, LineSpan) for Value in SlabValue.Loops[0]
    ):
        raise ValueError("Fusion drafts require one profile of straight sides")
    Height = SlabValue.UpperCm - SlabValue.LowerCm
    SpreadCm = Height * Tangent(Radians(Feature.AngleDegrees))
    Bottom, Summit = DraftLoops(SlabValue.Loops[0], SpreadCm, Operation)
    Renamed = {
        Before.Label: After.Label for Before, After in zip(SlabValue.Loops[0], Bottom)
    }
    Curves = tuple(
        (Renamed[Label], Curve)
        for Label, Curve in Solid.SketchCurves
        if Label in Renamed
    )
    Tracks = tuple((Renamed.get(Label, Label), Index) for Label, Index in Solid.Tracks)
    Drafted = ReplaceValue(SlabValue, Loops=(Bottom,), RoofLoops=(Summit,))
    return ReplaceValue(
        Solid,
        Slabs=(Drafted,),
        SketchCurves=Solid.SketchCurves + Curves,
        Tracks=Tracks,
    )
