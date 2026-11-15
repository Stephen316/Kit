from typing import TypedDict

from convert.adapters.solidworks.config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.config.Presentation import ReadModelTail
from convert.adapters.solidworks.config.Regions import KRegionRow
from convert.adapters.solidworks.config.RootAtoms import AtomEnd, EndGhosts
from convert.adapters.solidworks.config.RootEntry import EntryStop, FindEntry
from convert.adapters.solidworks.config.RootFields import ModelAtomStart
from convert.adapters.solidworks.config.RootLayout import (
    KConfigGen,
    ExtendRoot,
    LoadPartLayouts,
    PartLayouts,
)
from convert.adapters.solidworks.container.Archive import KDefinitionKind, ReadTag
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import (
    ArchiveCursor,
    KArchiveEvent,
)


# the resolved reader needs actual atom and relation boundaries independently of views
class ModelMapWalk(TypedDict):
    atom_count: int
    relation_manager: int
    pointers: list[KArchiveEvent]
    regions: list[list[KRegionRow]]


# the ordinary model may own a single inline atom before its empty relation manager
def ReadRelEntry(BlobValue: bytes, Stages: PartLayouts) -> tuple[EntryStop, int]:
    Model, Layouts = ReadModelEntry(BlobValue, Stages)
    ModelBody, AtomStart, Count = ModelAtomStart(BlobValue, Model)
    RequireArch(Count in (0, 1), True, "ordinary configuration atom count")
    if Count:
        TagValue = ReadTag(BlobValue, AtomStart)
        RequireArch(
            (TagValue.kind, TagValue.class_name, TagValue.schema),
            (KDefinitionKind, "moAtom_c", 1),
            "typed ordinary body atom",
        )
        AtomStop = AtomEnd(BlobValue, AtomStart + TagValue.size)
        Relation = EndGhosts(BlobValue, AtomStop + 4)
        Slots: tuple[str, ...] = ("moAtom_c", "moRelMgr_c")
        Widths: tuple[int, ...] = (AtomStart - ModelBody, Relation - AtomStop)
    else:
        Relation = EndGhosts(BlobValue, AtomStart + 4)
        Slots = ("moRelMgr_c",)
        Widths = (Relation - ModelBody,)
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
    BlobValue: bytes, Generation: int | None
) -> tuple[ArchiveCursor, ModelMapWalk]:
    RequireArch(Generation, KConfigGen, "supported configuration generation")
    Manager, Count = ReadRelEntry(BlobValue, LoadPartLayouts())
    BodyStart = Manager.offset + ReadTag(BlobValue, Manager.offset).size
    Cursor = ArchiveCursor(
        BlobValue, BodyStart, Manager.Counter, Manager.Classes, Manager.Objects
    )
    ReadEmptyRel(Cursor)
    Events, Regions = ReadModelTail(Cursor)
    return Cursor, {
        "atom_count": Count,
        "relation_manager": Manager.offset,
        "pointers": Events,
        "regions": Regions,
    }
