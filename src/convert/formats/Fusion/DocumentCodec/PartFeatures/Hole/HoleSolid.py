from dataclasses import replace as ReplaceValue
from math import radians as Radians, tan as Tangent

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    ProfileLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionMath import (
    RegionSide,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanCross import SpanCross

KHoleLimit = 1e-9


def HoleTop(Solid: PrismSolid, Feature: HoleSpec) -> float:
    Widest = (
        max(Feature.DiameterMm, Feature.BoreDiameterMm, Feature.SinkDiameterMm) / 2.0
    )
    LoopValue = ProfileLoop(
        (CircleCurve(Feature.CenterMm, Widest),), (Solid.BodyLabel,)
    )
    Ceiling = Solid.Slabs[-1]
    Center = (Feature.CenterMm[0] / 10.0, Feature.CenterMm[1] / 10.0)
    Crossed = any(
        SpanCross(LoopValue[0], Value) for Other in Ceiling.Loops for Value in Other
    )
    if Crossed or RegionSide(Ceiling.Loops, Center) <= 0:
        raise ValueError("Fusion holes must lie inside the top face")
    return Ceiling.UpperCm


def CircleSlab(
    Feature: HoleSpec,
    Bounds: tuple[float, float],
    Labels: tuple[FaceLabel, FaceLabel],
    DiameterMm: float,
) -> PrismSlab:
    Circle = CircleCurve(Feature.CenterMm, DiameterMm / 2.0)
    LoopValue = ProfileLoop((Circle,), Labels[:1])
    return PrismSlab(Bounds[0], Bounds[1], (LoopValue,), Labels[1], Labels[1])


def HoleLabels(Operation: int, Names: tuple[str, str]) -> tuple[FaceLabel, FaceLabel]:
    return FaceLabel(Names[0], (Operation,)), FaceLabel(Names[1], (Operation,))


def SinkDepth(Feature: HoleSpec) -> float:
    if not Feature.SinkDiameterMm:
        return 0.0
    Spread = (Feature.SinkDiameterMm - Feature.DiameterMm) / 2.0
    return Spread / Tangent(Radians(Feature.SinkAngleDegrees) / 2.0) / 10.0


def SinkSlab(
    Feature: HoleSpec, Bounds: tuple[float, float], Operation: int
) -> PrismSlab:
    Labels = HoleLabels(Operation, ("10", "10"))
    Narrow = CircleSlab(Feature, Bounds, Labels, Feature.DiameterMm)
    Widened = CircleSlab(Feature, Bounds, Labels, Feature.SinkDiameterMm)
    return ReplaceValue(Narrow, RoofLoops=Widened.Loops)


def HoleShapers(
    Solid: PrismSolid, Feature: HoleSpec, Operation: int
) -> tuple[PrismSlab, ...]:
    Ceiling = HoleTop(Solid, Feature)
    Bottom = Solid.Slabs[0].LowerCm
    Lower = Ceiling - Feature.DepthMm / 10.0 if Feature.DepthMm else Bottom
    Upper = Ceiling - Feature.BoreDepthMm / 10.0 - SinkDepth(Feature)
    if Lower < Bottom - KHoleLimit or (Feature.DepthMm and Lower <= Bottom):
        raise ValueError("Fusion blind holes must end inside the body")
    if Upper <= max(Lower, Bottom) + KHoleLimit:
        raise ValueError(
            "Fusion counterbores and countersinks must end inside the hole"
        )
    Shapers: list[PrismSlab] = []
    if Feature.SinkDiameterMm:
        Shapers.append(SinkSlab(Feature, (Upper, Ceiling), Operation))
    if Feature.BoreDepthMm:
        Labels = HoleLabels(Operation, ("7", "8"))
        Bounds = (Upper, Ceiling)
        Shapers.append(CircleSlab(Feature, Bounds, Labels, Feature.BoreDiameterMm))
    Labels = HoleLabels(Operation, ("3", "5"))
    Shapers.append(CircleSlab(Feature, (Lower, Upper), Labels, Feature.DiameterMm))
    return tuple(Shapers)


def HoleSolid(Solid: PrismSolid, Feature: HoleSpec, Operation: int) -> PrismSolid:
    Result = Solid
    for Shaper in HoleShapers(Solid, Feature, Operation):
        Result = ExtrudeSolid(Result, Shaper, "cut", None)
    return Result
