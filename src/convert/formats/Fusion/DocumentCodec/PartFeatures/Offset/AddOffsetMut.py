from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.TagState import (
    TagState,
)
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddPickMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    RoofRecipe,
    SideRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import (
    RoofTag,
    SideTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.OffsetLoop import (
    OffsetIndex,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


def OffsetFeature(Stage: PartStage) -> OffsetSpec:
    Feature = Stage.Feature
    if not isinstance(Feature, OffsetSpec):
        raise ValueError("Fusion offset authoring requires an offset feature")
    return Feature


def OffsetPick(
    Solids: tuple[TagState, ...], Place: int, Stage: PartStage
) -> tuple[RecipeValue, int]:
    Feature = OffsetFeature(Stage)
    if Feature.SideMm is None:
        return RoofRecipe(Stage.Before), RoofTag(Solids, Place)
    LoopValue = Stage.Before.Slabs[0].Loops[0]
    PointCm = (Feature.SideMm[0] / 10.0, Feature.SideMm[1] / 10.0)
    Index = OffsetIndex(LoopValue, PointCm)
    TagValue = SideTags(Solids, Place, (LoopValue[Index],))[0]
    return SideRecipe(Stage.Before, Index), TagValue


def AddOffsetMut(
    Author: AuthorState,
    Stage: PartStage,
    Prefix: str,
    Picked: tuple[RecipeValue, int],
) -> list[str]:
    Feature = OffsetFeature(Stage)
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcOffsetFacesFeature", None)
    Cache: dict[str, object] = {"cachedEntityId": Picked[1], "scope": PartScope(Author)}
    AddPickMut(Author, Prefix, Picked[0], 16, "ETCachedTopology", Cache)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    AddParamMut(
        Author, Prefix + "amount", MainRole, "distance", Feature.DistanceMm, "mm"
    )
    Author.Change(MainRole, rParamDistance=Author.Reference(Prefix + "amount"))
    return [Prefix + "target", Prefix + "pick", Prefix + "amount"]
