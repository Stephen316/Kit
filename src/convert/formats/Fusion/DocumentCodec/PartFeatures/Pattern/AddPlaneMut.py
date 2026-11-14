from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyRefs import (
    AddEntityRefMut,
    AddSeedMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PlaneFrame import (
    PlaneMatrix,
    PlaneValue,
)
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadSeries,
)

KWorkModes: dict[str, object] = dict(isVisibleBeforeRollback=True)
KPointModes: dict[str, object] = dict(KWorkModes, chainPropagation=True)
KPlaneModes: dict[str, object] = dict(KPointModes, isProportionalParam=True)


def LinkPlaneMut(Author: AuthorState, Prefix: str, Feature: PlaneSpec) -> None:
    Reference = Author.Reference
    Group = Author.FindEntity("work_geometries").FieldValues
    Count = ReadInteger(Group.get("highWaterMarkPlanes", 0)) + 1
    Members = list(ReadSeries(Group.get("groupChildren", [])))
    Author.Change(
        "work_geometries",
        highWaterMarkPlanes=Count,
        groupChildren=Members + [Reference(Prefix + "plane")],
    )
    Author.Change(
        Prefix + "plane",
        eCreationType=1,
        plane=PlaneValue(Feature, Feature.OffsetMm / 10.0),
        actIdentifier="0_" + str(Author.Roles[Prefix + "plane"]),
        groupParent=Reference("work_geometries"),
        id=Count,
        isOrigin=False,
        originName="",
        rDcNode=Reference(Prefix + "feature"),
        userName=Feature.FeatureName,
    )
    Author.Change(
        Prefix + "feature",
        extraOffset=Reference(Prefix + "extra"),
        rWorkPlane=Reference(Prefix + "plane"),
        rWorkPlaneMatrix=Reference(Prefix + "matrix"),
        **KPlaneModes,
    )


def AddPlaneMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, PlaneSpec):
        raise ValueError("Fusion plane authoring requires a plane feature")
    Reference = Author.Reference
    Owner, BaseRole = Prefix + "feature", Feature.BasePlane + "_plane"
    Author.Allocate(Prefix + "plane", "WorkPlane", ParentRole="work_geometries")
    AddNodeMut(Author, Owner, "DcWorkPlane", None)
    AddParamMut(
        Author, Prefix + "along", Owner, "AlongDistance", Feature.OffsetMm, "mm"
    )
    RefRole = AddEntityRefMut(Author, Prefix, "base", (BaseRole, 33))
    Cache: dict[str, object] = {
        "rCachedGeometry": PlaneValue(Feature, 0.0),
        "progenitor": AddSeedMut(Author, RefRole, BaseRole),
    }
    Author.Allocate(RefRole + "_cache", "ETCachedPlane", Fields=Cache)
    Author.Change(RefRole, caches=[Reference(RefRole + "_cache")])
    Fields: dict[str, object] = dict(
        dataRefs=[Reference(RefRole)],
        matrix3d={"entries": PlaneMatrix(Feature)},
        refType=2,
        values=[Reference(Prefix + "along")],
    )
    AddPlaceMut(Author, Prefix, ("matrix", "DRMatrix"), Fields)
    AddParamMut(Author, Prefix + "extra", Owner, "ExtraOffset", 0.0, "mm", "0.00 mm")
    Author.Change(Prefix + "matrix", extraOffset=Reference(Prefix + "extra"))
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    LinkPlaneMut(Author, Prefix, Feature)
    return [Prefix + "along", RefRole, Prefix + "matrix", Prefix + "extra"]
