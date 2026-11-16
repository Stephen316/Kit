from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# Save order differs from object order. Each member and initializer is in CmgrMiddle.md.
KListFields = (0, 1, 0, 0, 1)
KFloatDefaults = (-1.0, -1.0)
KArrayDefaults = (0, 0, 1, 0, *((0,) * 6), 1, 0, -1, 1, 0)
KFollowingMaps = (0, 0, 0, 0)
KPropertyLists = (0, 0, 0)


def RequireCollectionAtoms(Generation: int, AtomIds: tuple[int, ...]) -> None:
    RequireArch(
        type(Generation) is int and Generation == 19000,
        True,
        "CMgr collections generation",
    )
    RequireArch(
        len(AtomIds) <= 1
        and all(type(Atom) is int and 0 < Atom <= 0x7FFFFFFF for Atom in AtomIds),
        True,
        "CMgr standalone collections accept at most one owned atom",
    )


# The typed atom map gains a default entry before its separate linked node is saved.
def WriteCollections(
    Writer: ArchiveWriter, Generation: int, AtomIds: tuple[int, ...]
) -> None:
    RequireCollectionAtoms(Generation, AtomIds)
    Writer.raw(PackFields("<5i2f", *KListFields, *KFloatDefaults))
    Writer.raw(PackFields("<15i", *KArrayDefaults))
    Writer.u32(0)
    Writer.i32(0)
    Writer.i32(len(AtomIds))
    for Atom in AtomIds:
        Writer.i32(Atom)
        Writer.i32(0)
    Writer.raw(PackFields("<4i", *KFollowingMaps))
    Writer.u16(0)
    Writer.raw(PackFields("<3i", *KPropertyLists))
    Writer.raw(EncodeNull())
    Writer.i32(0)
    Writer.u32(0)


# The following links will establish that each default material entry owns a real atom.
def ReadCollections(Cursor: ArchiveCursor, Generation: int) -> tuple[int, ...]:
    RequireCollectionAtoms(Generation, ())
    RequireArch(Cursor.ReadInts("<5i"), KListFields, "CMgr standalone list flags")
    RequireArch(
        Cursor.ReadValue("<2f"), KFloatDefaults, "CMgr standalone configuration floats"
    )
    RequireArch(Cursor.ReadInts("<15i"), KArrayDefaults, "CMgr standalone arrays")
    RequireArch(Cursor.ReadInts("<Ii"), (0, 0), "CMgr empty visual maps")
    count = Cursor.ReadCount()
    RequireArch(count <= 1, True, "CMgr standalone atom material-state count")
    pairs = tuple(Cursor.ReadInts("<2i") for _ in range(count))
    atom_ids = tuple(atom for atom, _ in pairs)
    RequireCollectionAtoms(Generation, atom_ids)
    RequireArch(
        pairs, tuple((atom, 0) for atom in atom_ids), "CMgr default atom material state"
    )
    RequireArch(Cursor.ReadInts("<4i"), KFollowingMaps, "CMgr default following maps")
    RequireArch(Cursor.ReadInts("<H"), (0,), "CMgr empty string-to-int map")
    RequireArch(Cursor.ReadInts("<3i"), KPropertyLists, "CMgr default property lists")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<iI"), (0, 0), "CMgr default collection return")
    return atom_ids
