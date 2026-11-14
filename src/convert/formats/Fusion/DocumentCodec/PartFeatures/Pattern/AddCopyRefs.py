from math import hypot as Hypotenuse

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
    TopologyCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PlaneFrame import (
    PointOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)

KAxisRows: dict[str, tuple[float, float, float]] = {
    "x_axis": (2.0, 0.0, 0.0),
    "y_axis": (0.0, 2.0, 0.0),
    "z_axis": (0.0, 0.0, 2.0),
}


def UnitAxis(AxisRole: str) -> dict[str, float]:
    AxisRow = KAxisRows[AxisRole]
    Length = Hypotenuse(*AxisRow)
    return PointOf((AxisRow[0] / Length, AxisRow[1] / Length, AxisRow[2] / Length))


def AddSeedMut(
    Author: AuthorState, RoleName: str, EntityRole: str
) -> dict[str, object] | None:
    Entity: dict[str, object] = {"m_entityId": Author.Roles[EntityRole]}
    Author.Allocate(RoleName + "_entity", "EntityRecipe", Fields=Entity)
    SeedValue: dict[str, object] = {
        "m_entityRecipe": Author.Reference(RoleName + "_entity")
    }
    Author.Allocate(RoleName + "_seed", "EntityProgenitor", Fields=SeedValue)
    return Author.Reference(RoleName + "_seed")


def AddEntityRefMut(
    Author: AuthorState, Prefix: str, NameValue: str, Target: tuple[str, int]
) -> str:
    EntityRole, Tracking = Target
    RoleName = Prefix + NameValue
    AddNodeMut(Author, RoleName, "EntityDataRef", Prefix + "feature")
    Entity: dict[str, object] = {"m_entityId": Author.Roles[EntityRole]}
    Author.Allocate(RoleName + "_recipe", "EntityRecipe", Fields=Entity)
    Author.Change(
        RoleName,
        rRecipe=Author.Reference(RoleName + "_recipe"),
        rScope=PartScope(Author),
        trackingType=Tracking,
    )
    return RoleName


def AddAxisMut(
    Author: AuthorState, Prefix: str, NameValue: str, AxisRole: str
) -> list[str]:
    Reference = Author.Reference
    Origin = PointOf((0.0, 0.0, 0.0))
    Shift = PointOf(KAxisRows[AxisRole])
    LineValue = {"pointOnLine": Origin, "parametricDirection": Shift}
    Fields: dict[str, object] = dict(
        axisTrackType=8,
        line3d=LineValue,
        param={"x": 0.0, "y": 0.0},
        refType=7,
        resizeType=0,
    )
    AddPlaceMut(Author, Prefix, (NameValue, "DRVector"), Fields)
    RefRole = AddEntityRefMut(Author, Prefix, NameValue + "_ref", (AxisRole, 33))
    Cache: dict[str, object] = {
        "rCachedGeometry": {"startPoint": Origin, "displacement": Shift},
        "progenitor": AddSeedMut(Author, RefRole, AxisRole),
    }
    Author.Allocate(RefRole + "_cache", "ETCachedLineSeg3d", Fields=Cache)
    Author.Change(RefRole, caches=[Reference(RefRole + "_cache")])
    Author.Change(Prefix + NameValue, dataRefs=[Reference(RefRole)])
    return [Prefix + NameValue, RefRole]


def AddBodyCacheMut(Author: AuthorState, RoleName: str, TagValue: int) -> None:
    TopologyCache(Author, RoleName, TagValue)
    Author.Change(
        RoleName, progenitor=AddSeedMut(Author, RoleName, FocusRole(Author, "dc_body"))
    )


def AddSourceMut(
    Author: AuthorState, Prefix: str, SourceRole: str, TagSet: tuple[int, int, int]
) -> list[str]:
    Reference = Author.Reference
    Owner = Prefix + "feature"
    AddNodeMut(Author, Prefix + "source_set", "DcPatternSource", Owner)
    AddPlaceMut(Author, Prefix, ("source", "ModelDataRef"), {})
    RefRole = AddEntityRefMut(Author, Prefix, "source_ref", (SourceRole, 4))
    Author.Change(RefRole, refBodies=[Reference(FocusRole(Author, "dc_body"))])
    Author.Change(Prefix + "source", dataRefs=[Reference(RefRole)])
    AddBodyCacheMut(Author, Prefix + "source_body", TagSet[1])
    Bodies = [Reference(Prefix + "source_body")]
    Author.Change(
        Prefix + "source_set",
        caches=[{"first": Reference(RefRole), "second": Bodies}],
        patternFeature=Reference(Owner),
    )
    return [Prefix + "source_set", Prefix + "source", RefRole]


def AddAdjacentMut(Author: AuthorState, Prefix: str, FaceTag: int) -> None:
    AddBodyCacheMut(Author, Prefix + "adjacent_cache", FaceTag)
    Adjacent = [Author.Reference(Prefix + "adjacent_cache")]
    Author.Change(Prefix + "source_set", adjacentFaceCaches=Adjacent)
