from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.BodyStage import (
    KBodySpecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.CheckBodies import (
    CheckBodySpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.CheckExtrude import (
    CheckExtrude,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.CheckHole import CheckHole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Loft.CheckLoft import CheckLoft
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Sweep.CheckSweep import (
    CheckSweep,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.CheckCopy import (
    CheckCopy,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Move.CheckMove import CheckMove
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Draft.CheckDraft import (
    CheckDraft,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.CheckOffset import (
    CheckOffset,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Revolve.CheckRevolve import (
    CheckRevolve,
)

KFeatureLimit = 16
KCornerLimit = 8
KLinkedSpecs = (PatternSpec, CircularSpec, MirrorSpec, PlaneSpec)


def FeatureAmounts(Feature: KPartFeature) -> tuple[object, ...]:
    if isinstance(Feature, FilletSpec):
        return (*Feature.CornerMm, Feature.RadiusMm)
    if isinstance(Feature, ChamferSpec):
        return (*Feature.CornerMm, Feature.DistanceMm)
    if isinstance(Feature, ShellSpec):
        return (Feature.ThicknessMm,)
    return ()


def CheckName(NameValue: object) -> None:
    if (
        not isinstance(NameValue, str)
        or not NameValue
        or len(NameValue) > 1024
        or "\x00" in NameValue
    ):
        raise ValueError("Invalid Fusion part feature name")


def CheckPair(Point: object) -> None:
    if not isinstance(Point, tuple):
        raise ValueError("Fusion part corners require two planar coordinates")
    Coordinates = CastValue(tuple[object, ...], Point)
    if len(Coordinates) != 2:
        raise ValueError("Fusion part corners require two planar coordinates")
    for Value in Coordinates:
        if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
            raise ValueError("Fusion part feature values must be finite numbers")


def CheckCorners(Feature: FilletSpec | ChamferSpec) -> None:
    Extras = CastValue(object, Feature.MoreCornersMm)
    if not isinstance(Extras, tuple):
        raise ValueError("Fusion corner edits require a tuple of corners")
    Points = CastValue(tuple[object, ...], Extras)
    if len(Points) >= KCornerLimit:
        raise ValueError("Fusion corner edits take at most eight corners")
    for Point in Points:
        CheckPair(Point)
    Corners = (Feature.CornerMm, *Feature.MoreCornersMm)
    if len(set(Corners)) != len(Corners):
        raise ValueError("Fusion corner edits require distinct corners")


def CheckLevel(Feature: FilletSpec | ChamferSpec) -> None:
    Level = CastValue(object, Feature.LevelMm)
    if Level is None:
        return
    if type(Level) not in (int, float) or not IsFinite(CastValue(float, Level)):
        raise ValueError("Fusion edge round levels must be finite numbers")


def CheckSides(Feature: ShellSpec) -> None:
    Extras = CastValue(object, Feature.SidesMm)
    if not isinstance(Extras, tuple):
        raise ValueError("Fusion shell sides require a tuple of points")
    Points = CastValue(tuple[object, ...], Extras)
    if len(Points) >= KCornerLimit:
        raise ValueError("Fusion shell edits take at most seven open sides")
    for Point in Points:
        CheckPair(Point)
    if len(set(Feature.SidesMm)) != len(Points):
        raise ValueError("Fusion shell sides must be distinct")


def CheckShape(Feature: KPartFeature) -> None:
    if isinstance(Feature, (FilletSpec, ChamferSpec)):
        CheckCorners(Feature)
        CheckLevel(Feature)
    if isinstance(Feature, ChamferSpec):
        CheckBevel(Feature)
    if isinstance(Feature, ShellSpec):
        CheckSides(Feature)


def CheckBevel(Feature: ChamferSpec) -> None:
    Extras = (
        CastValue(object, Feature.SecondMm),
        CastValue(object, Feature.AngleDegrees),
    )
    for Value in Extras:
        if type(Value) not in (int, float) or not IsFinite(CastValue(float, Value)):
            raise ValueError("Fusion chamfer values must be finite numbers")
    if min(Feature.SecondMm, Feature.AngleDegrees) < 0:
        raise ValueError("Fusion chamfer values must not be negative")
    if min(Feature.SecondMm, Feature.AngleDegrees) > 0 or Feature.AngleDegrees >= 90:
        raise ValueError("Fusion chamfers take a second distance or an acute angle")


def CheckOwned(Feature: MoveSpec | OffsetSpec | HoleSpec | DraftSpec) -> None:
    if isinstance(Feature, MoveSpec):
        CheckMove(Feature)
    elif isinstance(Feature, DraftSpec):
        CheckDraft(Feature)
    elif isinstance(Feature, OffsetSpec):
        CheckOffset(Feature)
    else:
        CheckHole(Feature)


def HasSketchRule(Feature: KPartFeature) -> bool:
    if isinstance(Feature, ExtrudeSpec):
        CheckExtrude(Feature)
    elif isinstance(Feature, RevolveSpec):
        CheckRevolve(Feature)
    elif isinstance(Feature, LoftSpec):
        CheckLoft(Feature)
    elif isinstance(Feature, SweepSpec):
        CheckSweep(Feature)
    else:
        return False
    return True


def CheckFeature(Feature: KPartFeature) -> None:
    _ = FamilyOf(Feature)
    if HasSketchRule(Feature):
        return
    CheckName(CastValue(object, Feature.FeatureName))
    if isinstance(Feature, KBodySpecs):
        CheckBodySpec(Feature)
        return
    if isinstance(Feature, (MoveSpec, OffsetSpec, HoleSpec, DraftSpec)):
        CheckOwned(Feature)
        return
    if isinstance(Feature, (AxisSpec, PointSpec)):
        CheckPair(CastValue(object, Feature.CornerMm))
        return
    if isinstance(Feature, KLinkedSpecs):
        return
    Amounts = FeatureAmounts(Feature)
    if not isinstance(Feature, ShellSpec) and len(Amounts) != 3:
        raise ValueError("Fusion part corners require two planar coordinates")
    for Amount in Amounts:
        if type(Amount) not in (int, float) or not IsFinite(CastValue(float, Amount)):
            raise ValueError("Fusion part feature values must be finite numbers")
    if CastValue(float, Amounts[-1]) <= 0:
        raise ValueError("Fusion part feature sizes must be positive")
    CheckShape(Feature)


def IsNewBody(Feature: KPartFeature) -> bool:
    if isinstance(Feature, (LoftSpec, SweepSpec)):
        return True
    if not isinstance(Feature, (ExtrudeSpec, RevolveSpec)):
        return False
    return Feature.Operation == "new"


def CheckOrder(SpecValue: DocumentSpec) -> None:
    Features = SpecValue.Features
    IsPart = SpecValue.ProfileKind == "part"
    if IsPart and not IsNewBody(Features[0]):
        raise ValueError("Fusion part bodies start with a new solid")
    Extra = [
        Index
        for Index, Feature in enumerate(Features)
        if isinstance(Feature, KBodySpecs)
        or ((Index or not IsPart) and IsNewBody(Feature))
    ]
    if Extra and not IsPart:
        raise ValueError("Fusion multi-body features need a sketched part")
    IsMoved = False
    for Index, Feature in enumerate(Features):
        if isinstance(Feature, ShellSpec) and Index != len(Features) - 1:
            raise ValueError("Fusion part shell must be the final feature")
        if isinstance(Feature, HoleSpec) and IsMoved:
            raise ValueError("Fusion part holes cannot follow a move")
        IsMoved = IsMoved or isinstance(Feature, MoveSpec)


def CheckFeatures(SpecValue: DocumentSpec) -> None:
    Features = CastValue(object, SpecValue.Features)
    if not isinstance(Features, tuple):
        raise ValueError("Fusion part features must be a tuple")
    if SpecValue.ProfileKind == "part" and not Features:
        raise ValueError("Fusion part documents require features")
    if not Features:
        return
    if SpecValue.ProfileKind not in ("cuboid", "part") or SpecValue.ConstrainRectangle:
        raise ValueError(
            "Fusion part features require a part or an unconstrained cuboid"
        )
    if len(SpecValue.Features) > KFeatureLimit:
        raise ValueError("Fusion part feature count exceeds the qualified limit")
    for Index, Feature in enumerate(SpecValue.Features):
        CheckFeature(Feature)
        CheckCopy(SpecValue.Features, Index)
    CheckOrder(SpecValue)
    NameValue = SpecValue.ParamName
    if NameValue.startswith("d") and NameValue[1:].isdigit():
        raise ValueError("Fusion part features reserve generated parameter names")
