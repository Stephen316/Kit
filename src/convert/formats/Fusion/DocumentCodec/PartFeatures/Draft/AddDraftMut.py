from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.TagState import (
    TagState,
)
from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddBrepRefMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    SideRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import (
    CapTagSet,
    SideTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    PickFace,
    RecipeTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    LoopPolygon,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue

KDraftTags = tuple[tuple[int, ...], int]
KDraftModes: dict[str, object] = dict(
    MovingPartingLineDraftAngleType=3,
    draftType=1,
    m_bTangentPropagation=True,
    m_directionType=1,
    m_fixedPlaneDraftAngleMode=1,
)


def DraftTags(Solids: tuple[TagState, ...], Place: int, Stage: PartStage) -> KDraftTags:
    LoopValue = Stage.Before.Slabs[0].Loops[0]
    return SideTags(Solids, Place, LoopValue), CapTagSet(Solids, Place, False)[0]


def FloorCentre(Solid: PrismSolid) -> dict[str, float]:
    Polygon = LoopPolygon(Solid.Slabs[0].Loops[0])
    Twice = sum(
        Start[0] * Finish[1] - Finish[0] * Start[1]
        for Start, Finish in zip(Polygon, Polygon[1:] + Polygon[:1])
    )
    Centres = [
        sum(
            (Start[AxisValue] + Finish[AxisValue])
            * (Start[0] * Finish[1] - Finish[0] * Start[1])
            for Start, Finish in zip(Polygon, Polygon[1:] + Polygon[:1])
        )
        / (3.0 * Twice)
        for AxisValue in (0, 1)
    ]
    return {"x": Centres[0], "y": Centres[1]}


def AddDraftRefsMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: KDraftTags
) -> list[str]:
    MainRole = Prefix + "feature"
    AddNodeMut(Author, Prefix + "target", "ModelDataRef", MainRole)
    AddNodeMut(Author, Prefix + "plane", "ModelDataRef", MainRole)
    Roles: list[str] = []
    for Index, TagValue in enumerate(TagSet[0]):
        Cache: dict[str, object] = {
            "cachedEntityId": TagValue,
            "scope": PartScope(Author),
        }
        Names = (MainRole, Prefix + "side" + str(Index + 1))
        Recipe = SideRecipe(Stage.Before, Index)
        Roles.append(
            AddBrepRefMut(Author, Names, Recipe, ("ETCachedTopology", Cache, 16))
        )
    Floor = Stage.Before.Slabs[0].FloorLabel
    Recipe = RecipeValue(3, RecipeTags([Floor]), (), PickFace(0))
    Cache = {"cachedEntityId": TagSet[1], "scope": PartScope(Author)}
    Names = (MainRole, Prefix + "floor")
    _ = AddBrepRefMut(Author, Names, Recipe, ("ETCachedTopology", Cache, 33))
    Reference = Author.Reference
    for RoleName, Picks, Tracking in (
        (Prefix + "target", Roles, 16),
        (Prefix + "plane", [Prefix + "floor"], 33),
    ):
        Author.Allocate(RoleName + "_cache", "ETCachedMatrix3d")
        Author.Change(
            RoleName,
            dataRefs=[Reference(Value) for Value in Picks],
            caches=[Reference(RoleName + "_cache")],
            trackingType=Tracking,
        )
    return [Prefix + "target", *Roles, Prefix + "plane", Prefix + "floor"]


def AddDraftMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: KDraftTags
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, DraftSpec):
        raise ValueError("Fusion draft authoring requires a draft feature")
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcDraftFeature", None)
    Children = AddDraftRefsMut(Author, Stage, Prefix, TagSet)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Expression = ExprText(Feature.AngleDegrees) + " deg"
    Amount = Radians(Feature.AngleDegrees)
    AddParamMut(Author, Prefix + "angle", MainRole, "Angle1", Amount, "deg", Expression)
    AddParamMut(Author, Prefix + "other", MainRole, "Angle2", 0.0, "deg", "0.0 deg")
    Reference = Author.Reference
    Author.Change(
        MainRole,
        m_draftAngle1=Reference(Prefix + "angle"),
        m_draftAngle2=Reference(Prefix + "other"),
        m_rRefPlaneDataRef=Reference(Prefix + "plane"),
        m_facePickPoint=FloorCentre(Stage.Before),
        **KDraftModes,
    )
    return [*Children, Prefix + "angle", Prefix + "other"]
