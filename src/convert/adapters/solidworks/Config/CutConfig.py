from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.CutEqBody import ReadCutEq
from convert.adapters.solidworks.Config.CutEquation import ConfigSketch, CutEquation
from convert.adapters.solidworks.Config.OrdinaryMap import ModelMapWalk, ReadRelEntry
from convert.adapters.solidworks.Config.Presentation import ReadModelTail
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ReadTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# resolved feature evaluation needs the entire configuration map and named equation owners
@Dataclass(frozen=True, slots=True)
class CutConfig:
    Cursor: ArchiveCursor
    WalkValue: ModelMapWalk
    Equations: tuple[CutEquation, CutEquation]
    Sketches: dict[int, ConfigSketch]
    RelationEnd: int
    RelationNext: int


# later cuts can use only the two distinct owner dimensions from this same source pair
def CheckCenterPair(
    First: CutEquation, Second: CutEquation, Sketches: dict[int, ConfigSketch]
) -> None:
    RequireArch(len(Sketches), 2, "two reached equation sketches")
    RequireArch(
        (First.Target.SketchIndex, First.OuterTerm.SketchIndex),
        (Second.Target.SketchIndex, Second.OuterTerm.SketchIndex),
        "both equations use the same cut and outer sketch",
    )
    RequireArch(
        {
            First.Target.DimensionSlot,
            Second.Target.DimensionSlot,
            First.InnerTerm.DimensionSlot,
            Second.InnerTerm.DimensionSlot,
        },
        set(range(4)),
        "four distinct cut dimension slots",
    )
    RequireArch(
        {First.OuterTerm.DimensionSlot, Second.OuterTerm.DimensionSlot},
        {0, 1},
        "two distinct outer sketch dimension slots",
    )


# the relation manager returns its cursor for the configuration presentation walk
def ReadCutRel(
    BlobValue: bytes, Generation: int | None
) -> tuple[
    ArchiveCursor, tuple[CutEquation, CutEquation], dict[int, ConfigSketch], int
]:
    RequireArch(Generation, KConfigGen, "supported cut configuration generation")
    Manager, _ = ReadRelEntry(BlobValue, LoadPartLayouts(), (2,))
    BodyStart = Manager.offset + ReadTag(BlobValue, Manager.offset).size
    Cursor = ArchiveCursor(
        BlobValue, BodyStart, Manager.Counter, Manager.Classes, Manager.Objects
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two saved centering equations")
    Sketches: dict[int, ConfigSketch] = {}
    First, Second = ReadCutEq(Cursor, Sketches, 0), ReadCutEq(Cursor, Sketches, 1)
    CheckCenterPair(First, Second, Sketches)
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent extra relation parameter list")
    RequireArch(Cursor.ReadText(), "", "empty relation manager label")
    RequireArch(
        Cursor.ReadInts("<4iH2i"),
        (0, 0, 1, 1, 0, -1, 0),
        "guarded relation manager return",
    )
    return Cursor, (First, Second), Sketches, Manager.offset


# only the complete relation manager and model suffix establish the resolved map boundary
def ReadCutConfig(BlobValue: bytes, Generation: int | None) -> CutConfig:
    Cursor, Equations, Sketches, ManagerOffset = ReadCutRel(BlobValue, Generation)
    RelationEnd, RelationNext = Cursor.Offset, Cursor.NextIndex
    Events, Regions = ReadModelTail(Cursor)
    return CutConfig(
        Cursor,
        {
            "atom_count": 2,
            "relation_manager": ManagerOffset,
            "pointers": Events,
            "regions": Regions,
        },
        Equations,
        Sketches,
        RelationEnd,
        RelationNext,
    )
