from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchFrame import (
    FrameAxes,
    FrameMatrix,
)
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def AddPlaneCache(
    Author: AuthorState, Prefix: str, PlaneRole: str, LiftCm: float = 0.0
) -> None:
    Reference = Author.Reference
    Author.Allocate(Prefix + "plane_recipe", "EntityRecipe")
    Author.Allocate(Prefix + "plane_cache", "ETCachedPlane")
    Author.Allocate(Prefix + "matrix_cache", "ETCachedMatrix3d")
    Author.Allocate(Prefix + "plane_seed", "EntityProgenitor")
    Author.Allocate(Prefix + "plane_seed_recipe", "EntityRecipe")
    PlaneId = Author.Roles[PlaneRole]
    Author.Change(Prefix + "plane_recipe", m_entityId=PlaneId)
    Author.Change(Prefix + "plane_seed_recipe", m_entityId=PlaneId)
    Author.Change(
        Prefix + "plane_seed", m_entityRecipe=Reference(Prefix + "plane_seed_recipe")
    )
    AxisU, AxisV = FrameAxes(PlaneRole, LiftCm)
    PlaneValue = dict(
        normalReversed=False,
        origin=MakePoint(0.0, 0.0, LiftCm),
        uAxis=AxisU,
        vAxis=AxisV,
    )
    Author.Change(
        Prefix + "plane_cache",
        rCachedGeometry=PlaneValue,
        progenitor=Reference(Prefix + "plane_seed"),
    )


def AddSketchNode(
    Author: AuthorState,
    Prefix: str,
    Ordinal: int,
    PlaneRole: str,
    LiftCm: float = 0.0,
) -> None:
    Reference = Author.Reference
    MainRole = Prefix + "dc_sketch"
    AddNodeMut(Author, MainRole, "DcSketch", None)
    Author.Allocate(Prefix + "sketch_table", "ProgenitorTable")
    AddNodeMut(Author, Prefix + "plane", "EntityDataRef", MainRole)
    AddNodeMut(Author, Prefix + "matrix", "DRMatrix", MainRole)
    AddPlaneCache(Author, Prefix, PlaneRole, LiftCm)
    Author.Change(
        MainRole,
        rSketch=Reference(Prefix + "sketch"),
        rSketchPlaneMatrix=Reference(Prefix + "matrix"),
        childNodes=[Reference(Prefix + "plane"), Reference(Prefix + "matrix")],
        featureBaseName="Sketch",
        featureIndex=Ordinal,
        rProgenitorTable=Reference(Prefix + "sketch_table"),
        isVisibleBeforeRollback=False,
    )
    Author.Change(
        Prefix + "plane",
        rRecipe=Reference(Prefix + "plane_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(Prefix + "plane_cache")],
        trackingType=33,
        updateFlag=4,
    )
    Author.Change(
        Prefix + "matrix",
        dataRefs=[Reference(Prefix + "plane")],
        caches=[Reference(Prefix + "matrix_cache")],
        trackingType=4,
    )
    Matrix = FrameMatrix(PlaneRole, LiftCm)
    if Matrix:
        Author.Change(Prefix + "matrix", matrix3d=Matrix)
    Author.Change(Prefix + "sketch", rDcNode=Reference(MainRole))
