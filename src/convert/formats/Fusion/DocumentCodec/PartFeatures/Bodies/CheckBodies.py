from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.BodyStage import (
    KBodySpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.CheckCopy import (
    CheckShape,
)

KBodyLimit = 16
KCombineKinds = ("join", "cut", "intersect")


def CheckOrdinal(Value: object) -> None:
    if type(Value) is not int or not 1 <= Value <= KBodyLimit:
        raise ValueError("Fusion body numbers must be qualified positive integers")


def CheckCombine(Feature: CombineSpec) -> None:
    CheckOrdinal(Feature.TargetBody)
    Tools = CastValue(object, Feature.ToolBodies)
    if not isinstance(Tools, tuple) or not 1 <= len(CastValue(tuple[object], Tools)):
        raise ValueError("Fusion combines need a tuple of tool bodies")
    for Ordinal in CastValue(tuple[object, ...], Tools):
        CheckOrdinal(Ordinal)
    if Feature.Operation not in KCombineKinds:
        raise ValueError("Fusion combines join, cut or intersect")
    if type(CastValue(object, Feature.KeepTools)) is not bool:
        raise ValueError("Fusion combine tool keeping is a boolean")


def CheckBodySpec(Feature: KBodySpec) -> None:
    if isinstance(Feature, CombineSpec):
        CheckCombine(Feature)
        return
    if isinstance(Feature, PasteSpec):
        CheckOrdinal(Feature.SourceBody)
        return
    if isinstance(Feature, BodyGridSpec):
        CheckOrdinal(Feature.SourceBody)
        CheckShape(
            PatternSpec(
                0,
                Feature.CountU,
                Feature.SpacingUMm,
                Feature.CountV,
                Feature.SpacingVMm,
            )
        )
        return
    if isinstance(Feature, BodyRingSpec):
        CheckOrdinal(Feature.SourceBody)
        CheckShape(CircularSpec(0, Feature.Count, Feature.TotalDegrees))
        return
    CheckOrdinal(Feature.TargetBody)
    if type(CastValue(object, Feature.PlaneIndex)) is not int:
        raise ValueError("Fusion splits name their plane by feature index")
