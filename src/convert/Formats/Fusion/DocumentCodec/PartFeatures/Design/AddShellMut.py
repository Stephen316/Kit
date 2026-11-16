from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.TagState import (
    TagState,
)
from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddBrepRefMut,
    AddPickMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofRecipe,
    SideRecipe,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import (
    RoofTag,
    SideTags,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.OpenShell import SideIndex

# the shell tags shape must stay shared so design feature construction uses one contract for compatible values
KShellTags = tuple[int, tuple[tuple[int, int], ...]]


# shell tags needs an explicit validity boundary so modeling operations retain their document and timeline ownership
def ShellTags(Solids: tuple[TagState, ...], Place: int, Stage: PartStage) -> KShellTags:
    Feature = Stage.Feature
    if not isinstance(Feature, ShellSpec):
        raise ValueError("Fusion part shell authoring requires a shell feature")
    LoopValue = Stage.Before.Slabs[0].Loops[0]
    Indices = tuple(
        SideIndex(LoopValue, (Point[0] / 10.0, Point[1] / 10.0))
        for Point in Feature.SidesMm
    )
    Spans = tuple(LoopValue[Index] for Index in Indices)
    TagSet = SideTags(Solids, Place, Spans)
    return RoofTag(Solids, Place), tuple(zip(Indices, TagSet))


# the sides operation needs a consistent construction rule so modeling operations retain their document and timeline ownership
def AddSidesMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: KShellTags
) -> list[str]:
    Roles: list[str] = []
    for Number, (Index, TagValue) in enumerate(TagSet[1]):
        Cache: dict[str, object] = {
            "cachedEntityId": TagValue,
            "scope": PartScope(Author),
        }
        Recipe = SideRecipe(Stage.Before, Index)
        Names = (Prefix + "feature", Prefix + "side" + str(Number + 1))
        Roles.append(
            AddBrepRefMut(Author, Names, Recipe, ("ETCachedTopology", Cache, 16))
        )
    Reference = Author.Reference
    Picks = [Reference(RoleName) for RoleName in (*Roles, Prefix + "pick")]
    Author.Change(Prefix + "target", dataRefs=Picks)
    return Roles


# the shell operation needs a consistent construction rule so modeling operations retain their document and timeline ownership
def AddShellMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, TagSet: KShellTags
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, ShellSpec):
        raise ValueError("Fusion part shell authoring requires a shell feature")
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcShellFeature", None)
    Cache: dict[str, object] = {"cachedEntityId": TagSet[0], "scope": PartScope(Author)}
    AddPickMut(Author, Prefix, RoofRecipe(Stage.Before), 16, "ETCachedTopology", Cache)
    Sides = AddSidesMut(Author, Stage, Prefix, TagSet)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    AddParamMut(
        Author, Prefix + "amount", MainRole, "innerThickness", Feature.ThicknessMm, "mm"
    )
    Author.Change(MainRole, rParamInnerThickness=Author.Reference(Prefix + "amount"))
    Ordered = (Prefix + "target", *Sides, Prefix + "pick", Prefix + "amount")
    return list(Ordered)
