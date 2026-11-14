from math import radians as Radians

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LevelPicks import (
    KLevelPick,
    LevelPicks,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddBrepRefMut,
    AddPickMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    CornerRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import FamilyOf
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage


def CornerCache(Stage: PartStage, CornerCm: tuple[float, float]) -> dict[str, object]:
    Lower = Stage.Before.Slabs[0].LowerCm
    Height = Stage.Before.Slabs[-1].UpperCm - Lower
    return {
        "rCachedGeometry": dict(
            startPoint={"x": CornerCm[0], "y": CornerCm[1], "z": Lower},
            displacement={"x": 0.0, "y": 0.0, "z": Height},
        )
    }


def AddBevelMut(
    Author: AuthorState, Prefix: str, Feature: ChamferSpec
) -> tuple[str, ...]:
    MainRole = Prefix + "feature"
    Amount = Feature.DistanceMm
    if Feature.SecondMm > 0:
        AddParamMut(Author, Prefix + "amount", MainRole, "Distance 1", Amount, "mm")
        Other = Feature.SecondMm
        AddParamMut(Author, Prefix + "other", MainRole, "Distance 2", Other, "mm")
        return ("other",)
    AddParamMut(Author, Prefix + "amount", MainRole, "Distance", Amount, "mm")
    if Feature.AngleDegrees <= 0:
        return ()
    Angle = Feature.AngleDegrees
    Expression = ExprText(Angle) + " deg"
    AddParamMut(
        Author,
        Prefix + "other",
        MainRole,
        "Rotate Angle",
        Radians(Angle),
        "deg",
        Expression,
    )
    return ("other",)


def CornerPicks(Stage: PartStage) -> list[KLevelPick]:
    Feature = Stage.Feature
    if not isinstance(Feature, (FilletSpec, ChamferSpec)):
        raise ValueError("Fusion part corner feature requires a fillet or chamfer")
    Corners = tuple(
        (CornerMm[0] / 10.0, CornerMm[1] / 10.0)
        for CornerMm in (Feature.CornerMm, *Feature.MoreCornersMm)
    )
    if Feature.LevelMm is not None:
        return LevelPicks(Stage.Before, Corners, Feature.LevelMm / 10.0)
    return [
        (
            CornerRecipe(Stage.Before, CornerCm),
            "ETCachedLineSeg3d",
            CornerCache(Stage, CornerCm),
        )
        for CornerCm in Corners
    ]


def AddPicksMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Picks: list[str] = []
    for Index, (Recipe, CacheClass, Cache) in enumerate(CornerPicks(Stage)):
        RoleName = Prefix + "pick" + ("" if Index == 0 else str(Index + 1))
        if Index == 0:
            AddPickMut(Author, Prefix, Recipe, 8, CacheClass, Cache)
        else:
            Roles = (Prefix + "feature", RoleName)
            _ = AddBrepRefMut(Author, Roles, Recipe, (CacheClass, Cache, 8))
        Picks.append(RoleName)
    Reference = Author.Reference
    Author.Change(
        Prefix + "target", dataRefs=[Reference(PickRole) for PickRole in Picks]
    )
    return Picks


def AddSeedsMut(Author: AuthorState, Prefix: str, Picks: list[str]) -> None:
    Reference = Author.Reference
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Pairs: list[dict[str, object]] = []
    for Index, PickRole in enumerate(Picks):
        SeedRole = Prefix + "seed" + ("" if Index == 0 else str(Index + 1))
        Recipe = Author.FindEntity(PickRole + "_recipe").FieldValues["m_Recipe"]
        Author.Allocate(SeedRole, "BrepProgenitor", NamedPairs=[])
        Author.Allocate(SeedRole + "_recipe", "ASMRecipe", Fields={"m_Recipe": Recipe})
        Author.Change(SeedRole, m_brepRecipe=Reference(SeedRole + "_recipe"))
        Pairs.append({"first": Reference(SeedRole), "second": Index + 1})
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Pairs, tagId=len(Picks) + 1)


def AddCornerMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, (FilletSpec, ChamferSpec)):
        raise ValueError("Fusion part corner feature requires a fillet or chamfer")
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, FamilyOf(Feature).ClassName, None)
    Picks = AddPicksMut(Author, Stage, Prefix)
    AddSeedsMut(Author, Prefix, Picks)
    Roles = [Prefix + "target", *Picks]
    if isinstance(Feature, FilletSpec):
        AddParamMut(Author, Prefix + "weight", MainRole, "TangencyWeight", 1.0, "")
        AddParamMut(
            Author, Prefix + "amount", MainRole, "Radius", Feature.RadiusMm, "mm"
        )
        return Roles + [Prefix + "weight", Prefix + "amount"]
    Extra = AddBevelMut(Author, Prefix, Feature)
    AddNodeMut(Author, Prefix + "data", "DcChamferData", MainRole, False)
    return Roles + [Prefix + NameValue for NameValue in ("amount", *Extra, "data")]
