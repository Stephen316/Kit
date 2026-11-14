from dataclasses import replace as ReplaceValue
from math import radians as Radians
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofFaceRecipe,
    RoofRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    AddTargetMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddFaceRefMut,
    AddPlaceMut,
    AddThroughMut,
    TopologyCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.CheckHole import (
    IsBored,
    IsSunk,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage

KThroughNote = "SavedHoleDepthInNonDistanceExtentsCase"
KCenterPoint = 6
KFacePoint = 17
KCenterTolerance = 1e-9
KHoleModes: dict[str, object] = dict(bInside1=True, bInside2=True, extendFaceOption=1)
KHoleParam: TypeAlias = tuple[dict[str, float], int]
KHolePlace: TypeAlias = tuple[tuple[int, int, int], tuple[float, float]]


def HoleSpot(Stage: PartStage, Feature: HoleSpec) -> dict[str, float]:
    Ceiling = Stage.Before.Slabs[-1].UpperCm
    return {
        "x": Feature.CenterMm[0] / 10.0,
        "y": Feature.CenterMm[1] / 10.0,
        "z": Ceiling,
    }


def AddSizesMut(Author: AuthorState, Prefix: str, Feature: HoleSpec) -> list[str]:
    Owner = Prefix + "feature"
    Roles: list[str] = []
    if Feature.DepthMm:
        AddParamMut(Author, Prefix + "depth", Owner, "HoleDepth", Feature.DepthMm, "mm")
        Roles.append(Prefix + "depth")
    Width = Feature.DiameterMm
    AddParamMut(Author, Prefix + "diameter", Owner, "HoleDiameter", Width, "mm")
    TipValue = (180.0, "180 deg") if Feature.DepthMm else (118.0, "118.0 deg")
    AddParamMut(
        Author,
        Prefix + "tip",
        Owner,
        "TipAngle",
        Radians(TipValue[0]),
        "deg",
        TipValue[1],
    )
    Roles.extend((Prefix + "diameter", Prefix + "tip"))
    if IsBored(Feature):
        BoreDepth, BoreWidth = Feature.BoreDepthMm, Feature.BoreDiameterMm
        AddParamMut(Author, Prefix + "bore_depth", Owner, "CBDepth", BoreDepth, "mm")
        AddParamMut(Author, Prefix + "bore_width", Owner, "CBDiameter", BoreWidth, "mm")
        Roles.extend((Prefix + "bore_depth", Prefix + "bore_width"))
    return Roles + AddSinkMut(Author, Prefix, Feature)


def AddSinkMut(Author: AuthorState, Prefix: str, Feature: HoleSpec) -> list[str]:
    if not IsSunk(Feature):
        return []
    Owner, Width = Prefix + "feature", Feature.SinkDiameterMm
    AddParamMut(Author, Prefix + "sink_width", Owner, "CSDiameter", Width, "mm")
    Angle = Feature.SinkAngleDegrees
    Expression = ExprText(Angle) + " deg"
    AddParamMut(
        Author,
        Prefix + "sink_angle",
        Owner,
        "CSAngle",
        Radians(Angle),
        "deg",
        Expression,
    )
    return [Prefix + "sink_width", Prefix + "sink_angle"]


def HoleParam(SpotValue: dict[str, float], Middle: tuple[float, float]) -> KHoleParam:
    Plane = {
        "x": SpotValue["x"] - Middle[0],
        "y": SpotValue["y"] - Middle[1],
    }
    if max(abs(Plane["x"]), abs(Plane["y"])) < KCenterTolerance:
        return {"x": 0.0, "y": 0.0}, KCenterPoint
    return Plane, KFacePoint


def AddHolePlaceMut(
    Author: AuthorState, Prefix: str, Stage: PartStage, Place: KHolePlace
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, HoleSpec):
        raise ValueError("Fusion hole authoring requires a hole feature")
    TagSet, Middle = Place
    Reference = Author.Reference
    SpotValue = HoleSpot(Stage, Feature)
    Plane, PointKind = HoleParam(SpotValue, Middle)
    IsCentered = PointKind == KCenterPoint
    Recipe = (RoofFaceRecipe if IsCentered else RoofRecipe)(Stage.Before)
    AddFaceRefMut(Author, Prefix, "spot_face", Recipe, (33, TagSet[1]))
    Fields: dict[str, object] = dict(point3d=SpotValue, refType=PointKind, param=Plane)
    Fields.update(dataRefs=[Reference(Prefix + "spot_face")])
    AddPlaceMut(Author, Prefix, ("spot", "DRPoint"), Fields)
    Direction = {"x": 0.0, "y": 0.0, "z": 1.0}
    LineValue = {"pointOnLine": SpotValue, "parametricDirection": Direction}
    Fields = dict(
        axisTrackType=8, line3d=LineValue, param=Plane, refType=19, resizeType=0
    )
    AddPlaceMut(Author, Prefix, ("axis", "DRVector"), Fields)
    AddFaceRefMut(
        Author, Prefix, "axis_face", RoofRecipe(Stage.Before), (17, TagSet[0])
    )
    Author.Change(Prefix + "axis", dataRefs=[Reference(Prefix + "axis_face")])
    return [
        Prefix + NameValue for NameValue in ("spot_face", "spot", "axis", "axis_face")
    ]


def AddHoleMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, Place: KHolePlace
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, HoleSpec):
        raise ValueError("Fusion hole authoring requires a hole feature")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcHoleFeature", None)
    Label = ReplaceValue(Stage.Before.BodyLabel, Merged=())
    Children = AddTargetMut(Author, Prefix, Label)
    Author.Change(Prefix + "target", trackingType=4)
    TagSet = Place[0]
    Children += AddHolePlaceMut(Author, Prefix, Stage, Place)
    Children += AddSizesMut(Author, Prefix, Feature)
    Extent = [] if Feature.DepthMm else AddThroughMut(Author, Prefix, Label, TagSet[1])
    AddNodeMut(Author, Prefix + "tool", "DcHoleToolBody", MainRole)
    TopologyCache(Author, Prefix + "tool_cache", TagSet[2])
    Author.Change(
        Prefix + "tool",
        rHoleFeature=Reference(MainRole),
        toolbodyCaches=[Reference(Prefix + "tool_cache")],
    )
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=[], tagId=1)
    LinkHoleMut(Author, Prefix, Feature, Extent)
    return Children + Extent + [Prefix + "tool"]


def LinkHoleMut(
    Author: AuthorState, Prefix: str, Feature: HoleSpec, Extent: list[str]
) -> None:
    Reference = Author.Reference
    IsCounterbored, IsCountersunk = IsBored(Feature), IsSunk(Feature)
    Author.Change(
        Prefix + "feature",
        holeType=2 if IsCountersunk else int(IsCounterbored),
        bThroughAll=not Feature.DepthMm,
        rHoleDepth=Reference(Prefix + "depth" if Feature.DepthMm else None),
        rHoleDiameter=Reference(Prefix + "diameter"),
        rTipAngle=Reference(Prefix + "tip"),
        rCBDepth=Reference(Prefix + "bore_depth" if IsCounterbored else None),
        rCBDiameter=Reference(Prefix + "bore_width" if IsCounterbored else None),
        rCSAngle=Reference(Prefix + "sink_angle" if IsCountersunk else None),
        rCSDiameter=Reference(Prefix + "sink_width" if IsCountersunk else None),
        rDRMultipleOrigins=[Reference(Prefix + "spot")],
        rDRNormal=Reference(Prefix + "axis"),
        rHoleToolBody=Reference(Prefix + "tool"),
        rToEntityRefs=[Reference(Extent[0])] if Extent else [],
        **KHoleModes,
    )
    if not Feature.DepthMm:
        NoteValue = {"name": KThroughNote, "metatype": "IntrinsicMetaTypedouble"}
        Author.FindEntity(Prefix + "feature").NamedPairs = [dict(NoteValue, value=1.0)]
