from dataclasses import replace as ReplaceValue
from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddExtrudeFeat import (
    StageRange,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddJoinSeed import (
    AddJoinSeedMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddRegionMut import (
    AddRegionMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddSeedsMut import (
    AddSeedsMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    AddTargetMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import (
    KBooleanCodes,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyRefs import (
    KAxisRows,
    AddEntityRefMut,
    AddSeedMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PlaneFrame import (
    PointOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchRecs import (
    AddSketchRecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Revolve.RevolveSolid import (
    KRevolveOrder,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag

KAxisRole = "z_axis"
KAxisTracking = 33
KRevolveModes: dict[str, object] = dict(extendFaceOption=2, isSolidOperation=True)


def SketchTags(Sketched: SketchPlan) -> list[dict[str, object]]:
    Corners = [Sketched.PointsCm[Segment.StartIndex or 0] for Segment in Sketched.Edges]
    Signed = sum(
        Corners[Index - 1][0] * Point[1] - Point[0] * Corners[Index - 1][1]
        for Index, Point in enumerate(Corners)
    )
    Direction = 1 if Signed < 0 else 0
    return [RectangleTag(Segment.CurveTag, Direction) for Segment in Sketched.Edges]


def AddAxisRefMut(Author: AuthorState, Prefix: str) -> list[str]:
    Reference = Author.Reference
    AddPlaceMut(Author, Prefix, ("axis", "ModelDataRef"), {})
    RefRole = AddEntityRefMut(Author, Prefix, "axis_ref", (KAxisRole, KAxisTracking))
    LineValue = {"startPoint": PointOf((0.0, 0.0, 0.0))}
    LineValue["displacement"] = PointOf(KAxisRows[KAxisRole])
    Cache: dict[str, object] = {
        "rCachedGeometry": LineValue,
        "progenitor": AddSeedMut(Author, RefRole, KAxisRole),
    }
    Author.Allocate(RefRole + "_cache", "ETCachedLineSeg3d", Fields=Cache)
    Author.Change(RefRole, caches=[Reference(RefRole + "_cache")])
    Author.Change(
        Prefix + "axis", dataRefs=[Reference(RefRole)], trackingType=KAxisTracking
    )
    return [Prefix + "axis", RefRole]


def AddRevolveSeeds(
    Author: AuthorState, Stage: PartStage, Prefix: str, Sketched: SketchPlan
) -> None:
    Feature = Stage.Feature
    if not isinstance(Feature, RevolveSpec):
        raise ValueError("Fusion revolve seeds require a revolve")
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Pairs = AddSeedsMut(Author, Prefix, Sketched, KRevolveOrder)
    Operations, Count = Stage.Operations[1:], len(KRevolveOrder)
    if Feature.Operation == "new":
        Pairs.append(AddBodyMut(Author, Prefix, Count, Operations))
    if Feature.Operation == "join":
        Label = ReplaceValue(Stage.Before.BodyLabel, Merged=())
        Pairs.append(AddJoinSeedMut(Author, Prefix, Count, Operations, Label))
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Pairs, tagId=len(Pairs) + 3)


def AddTurnParam(Author: AuthorState, Prefix: str, Feature: RevolveSpec) -> str:
    Expression = ExprText(Feature.AngleDegrees) + " deg"
    Amount = Radians(Feature.AngleDegrees)
    Owner = Prefix + "feature"
    AddParamMut(
        Author, Prefix + "angle", Owner, "AlongAngle", Amount, "deg", Expression
    )
    return Prefix + "angle"


def AddRevolveFeat(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Feature, Sketched = Stage.Feature, Stage.Sketch
    if not isinstance(Feature, RevolveSpec) or Sketched is None:
        raise ValueError("Fusion part revolve authoring requires a sketch plan")
    Reference, MainRole = Author.Reference, Prefix + "feature"
    Names = (Feature.SketchName, "xz_plane")
    AddSketchRecs(Author, Prefix, Sketched, Names, Sketched.Ordinal)
    AddNodeMut(Author, MainRole, "DcRevolveFeature", None)
    Author.FindEntity(MainRole).NamedPairs = []
    Children: list[str] = []
    if Feature.Operation != "new":
        Label = ReplaceValue(Stage.Before.BodyLabel, Merged=())
        Children.extend(AddTargetMut(Author, Prefix, Label))
    AddRegionMut(Author, Prefix, SketchTags(Sketched))
    Children.extend([Prefix + "profile", Prefix + "region"])
    Children.extend(AddAxisRefMut(Author, Prefix))
    Children.append(AddTurnParam(Author, Prefix, Feature))
    AddNodeMut(Author, Prefix + "tool", "DcRevolveToolBody", MainRole)
    Author.Change(Prefix + "tool", rRevolveFeature=Reference(MainRole))
    Children.append(Prefix + "tool")
    AddRevolveSeeds(Author, Stage, Prefix, Sketched)
    Start, Finish = StageRange(Author, Stage)
    Author.Change(
        MainRole,
        booleanOperation=KBooleanCodes[Feature.Operation],
        **KRevolveModes,
        rAlongAngle=Reference(Prefix + "angle"),
        rAxisDataRef=Reference(Prefix + "axis"),
        rRevolveToolBody=Reference(Prefix + "tool"),
        childNodes=[Reference(RoleName) for RoleName in Children],
        profileDataRefs=[Reference(Prefix + "profile")],
        featureBaseName="Revolve",
        featureUserName=Feature.FeatureName,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=Start,
        endModelHS=Finish,
    )
