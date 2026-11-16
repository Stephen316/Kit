from typing import TypedDict

from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.Presentation import ReadModelTail
from convert.adapters.solidworks.Config.Regions import KRegionRow
from convert.adapters.solidworks.Config.RootAtoms import AtomEnd, EndGhosts
from convert.adapters.solidworks.Config.RootEntry import EntryStop, FindEntry
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import (
    KConfigGen,
    ExtendRoot,
    LoadPartLayouts,
    PartLayouts,
)
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    KArchiveEvent,
)


# the resolved reader needs actual atom and relation boundaries independently of views
class ModelMapWalk(TypedDict):
    atom_count: int
    relation_manager: int
    pointers: list[KArchiveEvent]
    regions: list[list[KRegionRow]]


# the first atom is a schema definition and the next uses its established class
def SkipAtomList(BlobValue: bytes, AtomStart: int, Count: int) -> int:
    StopValue = AtomStart
    for Index in range(Count):
        TagValue = ReadTag(BlobValue, StopValue)
        if Index == 0:
            RequireArch(
                (TagValue.kind, TagValue.class_name, TagValue.schema),
                (KDefinitionKind, "moAtom_c", 1),
                "typed first configuration atom",
            )
        else:
            RequireArch(TagValue.kind, KClassRefKind, "typed later configuration atom")
        StopValue = AtomEnd(BlobValue, StopValue + TagValue.size)
    return StopValue


# the split lengths and shared archive map must agree on the relation manager boundary
def ReadRelEntry(
    BlobValue: bytes, Stages: PartLayouts, AllowedCounts: tuple[int, ...] = (0, 1)
) -> tuple[EntryStop, int]:
    Model, Layouts = ReadModelEntry(BlobValue, Stages)
    ModelBody, AtomStart, Count = ModelAtomStart(BlobValue, Model)
    RequireArch(Count in AllowedCounts, True, "supported configuration atom count")
    AtomStop = SkipAtomList(BlobValue, AtomStart, Count)
    Relation = EndGhosts(BlobValue, AtomStop + 4)
    Slots = ("moAtom_c",) * Count + ("moRelMgr_c",)
    Widths = (
        (AtomStart - ModelBody,) + (0,) * (Count - 1) + (Relation - AtomStop,)
        if Count
        else (Relation - ModelBody,)
    )
    Layouts = ExtendRoot(Layouts, Stages.Atoms, Slots, Widths)
    Manager = FindEntry(BlobValue, Layouts, "moRelMgr_c")
    RequireArch(Manager.offset, Relation, "typed relation manager boundary")
    return Manager, Count


# only empty relation state can take this configuration path without equation children
def ReadEmptyRel(Cursor: ArchiveCursor) -> None:
    RequireArch(Cursor.ReadValue("<2H"), (0, 0), "empty equations and parameters")
    RequireArch(Cursor.ReadText(), "", "empty relation manager label")
    RequireArch(
        Cursor.ReadInts("<4i"), (0, 0, 1, -1), "ordinary relation manager state"
    )
    RequireArch(Cursor.ReadInts("<Hii"), (0, -1, 0), "empty relation manager tails")


# an ordinary config returns its map only after the entire claimed stream is framed
def ReadOrdinaryMap(
    BlobValue: bytes, Generation: int | None, *, Scoped: bool = False
) -> tuple[ArchiveCursor, ModelMapWalk]:
    RequireArch(Generation, KConfigGen, "supported configuration generation")
    AllowedCounts = (3, 4) if Scoped else (0, 1)
    Manager, Count = ReadRelEntry(BlobValue, LoadPartLayouts(), AllowedCounts)
    BodyStart = Manager.offset + ReadTag(BlobValue, Manager.offset).size
    Cursor = ArchiveCursor(
        BlobValue, BodyStart, Manager.Counter, Manager.Classes, Manager.Objects
    )
    ReadEmptyRel(Cursor)
    Events, Regions = ReadModelTail(Cursor, Scoped=Scoped)
    return Cursor, {
        "atom_count": Count,
        "relation_manager": Manager.offset,
        "pointers": Events,
        "regions": Regions,
    }
