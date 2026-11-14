from dataclasses import replace as ReplaceValue
from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.HoleSolid import (
    HoleShapers,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    KPlacement,
    MoveSlab,
    ShiftLabel,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ToolSlab import (
    ToolEdgeTags,
    ToolLabels,
    ToolSlab,
)

KCopySpec = PatternSpec | CircularSpec | MirrorSpec
KEdgeTags = tuple[tuple[FaceLabel, float, FaceLabel], ...]
KSourceTool = tuple[tuple[PrismSlab, ...], tuple[tuple[FaceLabel, int], ...], KEdgeTags]


def CopyPlaces(Feature: KCopySpec, MirrorCm: float) -> list[KPlacement]:
    if isinstance(Feature, MirrorSpec):
        return [((2.0 * MirrorCm, 0.0), 0.0, True)]
    if isinstance(Feature, CircularSpec):
        Total = Radians(Feature.TotalDegrees)
        IsFull = abs(Feature.TotalDegrees - 360.0) < 1e-9
        StepAngle = Total / (Feature.Count if IsFull else Feature.Count - 1)
        Count = Feature.Count
        return [((0.0, 0.0), Index * StepAngle, False) for Index in range(1, Count)]
    return [
        (
            (Across * Feature.SpacingUMm / 10.0, Along * Feature.SpacingVMm / 10.0),
            0.0,
            False,
        )
        for Along in range(Feature.CountV)
        for Across in range(Feature.CountU)
        if Across or Along
    ]


def SourceTool(Source: PartStage) -> KSourceTool:
    Feature = Source.Feature
    First = Source.Operations[0]
    if isinstance(Feature, HoleSpec):
        return HoleShapers(Source.Before, Feature, First), (), ()
    if not isinstance(Feature, ExtrudeSpec) or Feature.Operation != "cut":
        raise ValueError("Fusion patterns copy cut extrudes and holes")
    if Source.Sketch is None:
        raise ValueError("Fusion pattern sources require a sketch plan")
    Labels = ToolLabels(Feature, First + 1)
    Curves = tuple(
        (Label, Segment.CurveTag) for Label, Segment in zip(Labels, Source.Sketch.Edges)
    )
    Tagged = ToolEdgeTags(Feature, First + 1, Source.Sketch.Edges[0].CurveTag)
    return (ToolSlab(Feature, First + 1),), Curves, Tagged


def SourceFaces(Shapers: tuple[PrismSlab, ...]) -> tuple[FaceLabel, ...]:
    Walls = tuple(
        Value.Label
        for Shaper in Shapers
        for LoopValue in Shaper.Loops
        for Value in LoopValue
    )
    CapLabels = tuple(
        Label
        for Shaper in Shapers
        for Label in (Shaper.FloorLabel, Shaper.RoofLabel)
        if Label not in Walls
    )
    return Walls + tuple(dict.fromkeys(CapLabels))


def CopySolid(
    Solid: PrismSolid,
    Feature: KCopySpec,
    Operation: int,
    Source: PartStage,
    Context: tuple[int, float],
) -> PrismSolid:
    Shapers, Curves, Tagged = SourceTool(Source)
    Result = Solid
    NewCurves: list[tuple[FaceLabel, int]] = []
    NewTags: list[tuple[FaceLabel, float, FaceLabel]] = []
    for Index, Place in enumerate(CopyPlaces(Feature, Context[1])):
        Extra = (Operation, Operation + Index + 1)
        for Shaper in Shapers:
            Result = ExtrudeSolid(Result, MoveSlab(Shaper, Place, Extra), "cut", None)
        NewCurves.extend((ShiftLabel(Label, Extra), Curve) for Label, Curve in Curves)
        NewTags.extend(
            (ShiftLabel(WallLabel, Extra), Level, ShiftLabel(Label, Extra))
            for WallLabel, Level, Label in Tagged
        )
    Tracks = tuple((Label, Context[0]) for Label in SourceFaces(Shapers))
    return ReplaceValue(
        Result,
        SketchCurves=Solid.SketchCurves + tuple(NewCurves),
        EdgeTags=Solid.EdgeTags + tuple(NewTags),
        Tracks=Solid.Tracks + Tracks,
    )
