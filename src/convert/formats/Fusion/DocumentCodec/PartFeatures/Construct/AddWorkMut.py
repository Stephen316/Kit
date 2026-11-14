from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Construct.WorkCorner import (
    AxisRecipe,
    PointRecipe,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddCornerMut import (
    CornerCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddPickMut import (
    AddBrepRefMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddPlaneMut import (
    KPointModes,
    KWorkModes,
)
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadSeries,
)

KAxisCreation = 4
KAxisPlace = 8
KPointPlace = 10
KEdgeTracking = 33
KVertexTracking = 513
KAxisThickness = 1.2999999523162842
KAxisBounds = (-0.1, 1.1)


def LinkWorkMut(
    Author: AuthorState,
    Prefix: str,
    NameValue: str,
    Counter: tuple[str, dict[str, object]],
) -> None:
    MarkName, Fields = Counter
    Reference = Author.Reference
    RoleName = Prefix + "work"
    Group = Author.FindEntity("work_geometries").FieldValues
    Count = ReadInteger(Group.get(MarkName, 0)) + 1
    Members = list(ReadSeries(Group.get("groupChildren", [])))
    Author.Change("work_geometries", **{MarkName: Count})
    Author.Change("work_geometries", groupChildren=Members + [Reference(RoleName)])
    Author.Change(
        RoleName,
        actIdentifier="0_" + str(Author.Roles[RoleName]),
        groupParent=Reference("work_geometries"),
        id=Count,
        isOrigin=False,
        originName="",
        rDcNode=Reference(Prefix + "feature"),
        userName=NameValue,
        **Fields,
    )


def EdgeLine(Stage: PartStage, CornerCm: tuple[float, float]) -> dict[str, object]:
    Lower = Stage.Before.Slabs[0].LowerCm
    Height = Stage.Before.Slabs[-1].UpperCm - Lower
    return dict(
        pointOnLine={"x": CornerCm[0], "y": CornerCm[1], "z": Lower},
        parametricDirection={"x": 0.0, "y": 0.0, "z": Height},
    )


def AddAxisMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, AxisSpec):
        raise ValueError("Fusion axis authoring requires an axis feature")
    CornerCm = (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0)
    Owner, Reference = Prefix + "feature", Author.Reference
    Author.Allocate(Prefix + "work", "WorkAxis", ParentRole="work_geometries")
    AddNodeMut(Author, Owner, "DcWorkAxis", None)
    Cache = CornerCache(Stage, CornerCm)
    Recipe = AxisRecipe(Stage.Before, CornerCm)
    Tracked = ("ETCachedLineSeg3d", Cache, KEdgeTracking)
    EdgeRole = AddBrepRefMut(Author, (Owner, Prefix + "pick"), Recipe, Tracked)
    AxisLine = EdgeLine(Stage, CornerCm)
    Fields: dict[str, object] = dict(
        axisTrackType=KAxisPlace,
        line3d=AxisLine,
        param={"x": 0.0, "y": 0.0},
        refType=KAxisPlace,
        dataRefs=[Reference(EdgeRole)],
    )
    AddPlaceMut(Author, Prefix, ("vector", "DRVector"), Fields)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(
        Owner,
        creationType=KAxisCreation,
        rWorkAxis=Reference(Prefix + "work"),
        rWorkAxisRef=Reference(Prefix + "vector"),
        **KWorkModes,
    )
    Shape: dict[str, object] = dict(
        line=AxisLine,
        lowerParam=KAxisBounds[0],
        upperParam=KAxisBounds[1],
        lineThickness=KAxisThickness,
    )
    LinkWorkMut(Author, Prefix, Feature.FeatureName, ("highWaterMarkAxes", Shape))
    return [Prefix + "vector", EdgeRole]


def AddPointMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, PointSpec):
        raise ValueError("Fusion point authoring requires a point feature")
    CornerCm = (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0)
    Owner, Reference = Prefix + "feature", Author.Reference
    Author.Allocate(Prefix + "work", "WorkPoint", ParentRole="work_geometries")
    AddNodeMut(Author, Owner, "DcWorkPoint", None)
    Corner: dict[str, object] = {
        "x": CornerCm[0],
        "y": CornerCm[1],
        "z": Stage.Before.Slabs[0].LowerCm,
    }
    Recipe = PointRecipe(Stage.Before, CornerCm)
    Cached: dict[str, object] = {"rCachedGeometry": Corner}
    Tracked = ("ETCachedPoint3d", Cached, KVertexTracking)
    VertexRole = AddBrepRefMut(Author, (Owner, Prefix + "pick"), Recipe, Tracked)
    Fields: dict[str, object] = dict(
        boundingboxIndex=0,
        param={"x": 0.0, "y": 0.0},
        point3d=Corner,
        refType=KPointPlace,
        dataRefs=[Reference(VertexRole)],
    )
    AddPlaceMut(Author, Prefix, ("place", "DRPoint"), Fields)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(
        Owner,
        creationType=0,
        rWorkPoint=Reference(Prefix + "work"),
        rWorkPointRef=Reference(Prefix + "place"),
        **KPointModes,
    )
    Shape: dict[str, object] = {"point": Corner}
    LinkWorkMut(Author, Prefix, Feature.FeatureName, ("highWaterMarkPoints", Shape))
    return [Prefix + "place", VertexRole]


def AddWorkMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    if isinstance(Stage.Feature, AxisSpec):
        return AddAxisMut(Author, Stage, Prefix)
    return AddPointMut(Author, Stage, Prefix)
