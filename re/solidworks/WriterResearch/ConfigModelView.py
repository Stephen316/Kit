from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite
from typing import cast as CastValue

from ConfigUnits import KUnitTable
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, KRootClass
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    EncodeNull,
    EncodeObjectRef,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the local unit component files a reference to its own enclosing model allocation
KUnitComponent = "moUnitComponent_c"


# the optional curvature cache has its own class and does not own model geometry
KCurvatureClass = "gcCurvatureObject_c"


# reference plane appearance comes from the model presentation object
KPlaneViewClass = "moTransRefPlaneData_c"


# authored graph semantics cannot supply these environment settings or their creation time
@DataClass(frozen=True)
class CurvatureView:
    Settings: tuple[float, float, float, float, float]
    CreatedFiletime: int


# the appearance of the datum planes is independent of their authored frames
@DataClass(frozen=True)
class PlaneView:
    ShowEdges: int
    ShowIntersections: int
    FrontColor: int
    BackColor: int
    Transparency: int
    IntersectionColor: int


# explicit optional ownership preserves the two observed model presentation paths
@DataClass(frozen=True)
class ConfigModelView:
    Curvature: CurvatureView | None
    Planes: PlaneView


# the seeded first class and completed unit table identify the existing model object
def ModelIndex(Generation: int, NextIndex: int, Classes: dict[str, int]) -> int:
    Root = Classes.get(KRootClass, 0)
    RequireArch(
        (Generation, NextIndex, Root, Classes.get(KUnitTable)),
        (KConfigGen, 43, 1, 8),
        "model presentation after owned unit table",
    )
    return Root + 1


# curvature and display values must be valid before the writer allocates their objects
def RequireView(State: ConfigModelView) -> None:
    Curvature = State.Curvature
    if Curvature is not None:
        RequireArch(
            len(Curvature.Settings) == 5 and all(map(IsFinite, Curvature.Settings)),
            True,
            "five finite native curvature settings",
        )
        RequireArch(
            type(Curvature.CreatedFiletime) is int
            and 0 < Curvature.CreatedFiletime < 1 << 63,
            True,
            "curvature creation FILETIME",
        )
    Plane = State.Planes
    RequireArch(
        all(
            type(Flag) is int and Flag in (0, 1)
            for Flag in (Plane.ShowEdges, Plane.ShowIntersections)
        ),
        True,
        "plane edge and intersection display selectors",
    )
    RequireArch(
        all(
            type(Color) is int and 0 <= Color <= 0xFFFFFF
            for Color in (Plane.FrontColor, Plane.BackColor, Plane.IntersectionColor)
        ),
        True,
        "reference plane RGB colors",
    )
    RequireArch(
        type(Plane.Transparency) is int and 0 <= Plane.Transparency <= 100,
        True,
        "reference plane transparency",
    )


# an absent curvature object leaves the next archive allocation available to the plane
def ReadCurvature(Cursor: ArchiveCursor) -> CurvatureView | None:
    if ReadTag(Cursor.BlobValue, Cursor.Offset).kind == KNullKind:
        Cursor.ReadNull()
        return None
    Cursor.TakePointer((KCurvatureClass,), KDefinitionKind, CompactOnly=True)
    Settings = CastValue(tuple[float, float, float, float, float], Cursor.ReadPoint(5))
    Low, High = Cursor.ReadInts("<2I")
    return CurvatureView(Settings, Low | (High << 32))


# the reader advances the live map into the later model fields without rebasing aliases
def ReadModelView(Cursor: ArchiveCursor, Generation: int) -> ConfigModelView:
    Classes = {Name: Index for Index, Name in Cursor.Classes.items()}
    Model = ModelIndex(Generation, Cursor.NextIndex, Classes)
    RequireArch(Cursor.Objects.get(Model), KRootClass, "allocated part model")
    Cursor.TakePointer((KUnitComponent,), KDefinitionKind, CompactOnly=True)
    _, _, Owner = Cursor.TakePointer((KRootClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(Owner, Model, "local model unit component owner")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent external component")
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "empty face visual collections")
    RequireArch(Cursor.ReadInts("<B"), (0,), "unexploded model")
    Curvature = ReadCurvature(Cursor)
    Cursor.TakePointer((KPlaneViewClass,), KDefinitionKind, CompactOnly=True)
    State = ConfigModelView(Curvature, PlaneView(*Cursor.ReadInts("<iiIIiI")))
    RequireView(State)
    return State


# curvature cache creation time is split into the native low and high words
def WriteCurvature(Writer: ArchiveWriter, Curvature: CurvatureView | None) -> None:
    if Curvature is None:
        Writer.raw(EncodeNull())
        return
    Writer.BeginObject(KCurvatureClass, 1)
    for Value in Curvature.Settings:
        Writer.f64(Value)
    Writer.u32(Curvature.CreatedFiletime & 0xFFFFFFFF)
    Writer.u32(Curvature.CreatedFiletime >> 32)


# standalone model presentation follows the same part and units allocator as the root
def WriteModelView(
    Writer: ArchiveWriter, Generation: int, State: ConfigModelView
) -> None:
    Model = ModelIndex(Generation, Writer.next_index, Writer.classes)
    RequireView(State)
    Writer.BeginObject(KUnitComponent, 1)
    Writer.raw(EncodeObjectRef(Model))
    Writer.u8(0)
    Writer.i32(0)
    Writer.i32(0)
    Writer.u8(0)
    WriteCurvature(Writer, State.Curvature)
    Plane = State.Planes
    Writer.BeginObject(KPlaneViewClass, 1)
    Writer.i32(Plane.ShowEdges)
    Writer.i32(Plane.ShowIntersections)
    Writer.u32(Plane.FrontColor)
    Writer.u32(Plane.BackColor)
    Writer.i32(Plane.Transparency)
    Writer.u32(Plane.IntersectionColor)
