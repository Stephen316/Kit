from math import isfinite as IsFinite
from typing import cast as CastValue

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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec

KCopyLimit = 64


def CheckCount(Value: object, Lowest: int) -> int:
    if type(Value) is not int or not Lowest <= Value <= KCopyLimit:
        raise ValueError("Fusion pattern counts must be qualified integers")
    return Value


def CheckAmount(Value: object, IsSigned: bool) -> float:
    if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
        raise ValueError("Fusion pattern sizes must be finite numbers")
    Amount = float(CastValue(float, Value))
    if not IsSigned and Amount <= 0:
        raise ValueError("Fusion pattern sizes must be positive")
    return Amount


def CheckIndex(Features: tuple[KPartFeature, ...], Value: object, Index: int) -> object:
    if type(Value) is not int or not 0 <= Value < Index:
        raise ValueError("Fusion pattern references must name an earlier feature")
    return Features[Value]


def CheckShape(Feature: PatternSpec | CircularSpec | PlaneSpec) -> None:
    if isinstance(Feature, PlaneSpec):
        _ = CheckAmount(Feature.OffsetMm, True)
        if Feature.BasePlane not in ("xy", "yz", "xz"):
            raise ValueError("Fusion offset planes start from an origin plane")
        return
    if isinstance(Feature, CircularSpec):
        _ = CheckCount(Feature.Count, 2)
        if CheckAmount(Feature.TotalDegrees, False) > 360.0:
            raise ValueError("Fusion circular patterns span at most one turn")
        return
    Product = CheckCount(Feature.CountU, 1) * CheckCount(Feature.CountV, 1)
    if not 2 <= Product <= KCopyLimit:
        raise ValueError("Fusion rectangular patterns need two to 64 instances")
    _ = CheckAmount(Feature.SpacingUMm, False)
    _ = CheckAmount(Feature.SpacingVMm, False)


def CheckCopy(Features: tuple[KPartFeature, ...], Index: int) -> None:
    Feature = Features[Index]
    if isinstance(Feature, (PatternSpec, CircularSpec, PlaneSpec)):
        CheckShape(Feature)
    if not isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        return
    Source = CheckIndex(Features, Feature.SourceIndex, Index)
    IsCut = isinstance(Source, ExtrudeSpec) and Source.Operation == "cut"
    if not IsCut and not isinstance(Source, HoleSpec):
        raise ValueError("Fusion patterns copy cut extrudes and holes")
    if isinstance(Feature, MirrorSpec):
        Plane = CheckIndex(Features, Feature.PlaneIndex, Index)
        if not isinstance(Plane, PlaneSpec) or Plane.BasePlane != "yz":
            raise ValueError("Fusion mirrors require an offset plane parallel to YZ")
