from hashlib import sha256

from CmgrLinks import WriteCmgrLinks
from CmgrPartEnd import ReadCmgrAliases, ReadCmgrPartEnd, WriteCmgrPartEnd
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import (
    KConfigClass,
    KExtObjectClass,
    KLinkClass,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

PART_LOCATIONS = {
    "P01": (1654, 1692, 1804, 9),
    "P03": (1662, 1758, 1878, 11),
    "P04": (1678, 1840, 1968, 12),
}


# the discovery atom nodes store their relation as keys with null pointer values
def read_link_keys(cursor: ArchiveCursor) -> tuple[int, ...]:
    count = cursor.ReadCount()
    RequireArch(count <= 1, True, "CMgr linked atom relation count")
    if count == 0:
        return ()
    keys = cursor.ReadInts("<i")
    cursor.ReadNull()
    return keys


# typed atom allocations prove that the part reader enters with the inherited map
def read_linked_atoms(
    cursor: ArchiveCursor, tree_ids: tuple[int, ...]
) -> tuple[int, ...]:
    count = cursor.ReadCount()
    RequireArch(count <= 2, True, "CMgr supported linked atom count")
    RequireArch(count, len(tree_ids), "CMgr linked atom count")
    links = {}
    for position in range(count):
        (key,) = cursor.ReadInts("<i")
        RequireArch(key > 0 and key not in links, True, "CMgr linked atom identity")
        kind = KDefinitionKind if position == 0 else KClassRefKind
        cursor.TakePointer((KLinkClass,), kind, CompactOnly=True)
        RequireArch(cursor.ReadInts("<iH"), (key, 1), "CMgr linked atom feature array")
        (tree_id,) = cursor.ReadInts("<I")
        RequireArch(cursor.ReadInts("<H"), (0,), "CMgr linked atom second array")
        links[key] = (tree_id, tuple(read_link_keys(cursor) for _ in range(4)))
    by_feature = sorted((tree_id, key) for key, (tree_id, _) in links.items())
    RequireArch(
        tuple(tree_id for tree_id, _ in by_feature), tree_ids, "CMgr linked feature IDs"
    )
    atoms = tuple(key for _, key in by_feature)
    if len(atoms) == 2:
        first, second = atoms
        relations = (((), (second,), (), (second,)), ((first,), (), (first,), ()))
    else:
        relations = (((), (), (), ()),) * len(atoms)
    RequireArch(
        tuple(links[key][1] for key in atoms), relations, "CMgr linked atom relations"
    )
    return atoms


# the base configuration closes independently of the following inline part record
def read_base_return(cursor: ArchiveCursor, atoms: tuple[int, ...]) -> None:
    RequireArch(cursor.ReadInts("<3i"), (0, 0, 0), "CMgr base collections")
    pairs = (tuple(reversed(atoms)),) if len(atoms) == 2 else ()
    count = cursor.ReadCount()
    RequireArch(count, len(pairs), "CMgr base pair count")
    RequireArch(tuple(cursor.ReadInts("<2i") for _ in pairs), pairs, "CMgr base pairs")
    RequireArch(cursor.ReadInts("<3i"), (2, 0, 0), "CMgr base closing fields")
    cursor.ReadNull()
    RequireArch(cursor.ReadInts("<i"), (0,), "CMgr base end vector")


# the readback must finish at the separately measured boundaries for every family
def read_part_evidence(
    cursor: ArchiveCursor, recipe: str, tree_ids: tuple[int, ...]
) -> tuple[tuple[int, ...], bytes, bytes]:
    linked_start, start, end, counter = PART_LOCATIONS[recipe]
    RequireArch((cursor.Offset, cursor.NextIndex), (1095, 9), "CMgr visual return map")
    cursor.Offset = linked_start
    atoms = read_linked_atoms(cursor, tree_ids)
    saved_links = cursor.BlobValue[linked_start : cursor.Offset]
    read_base_return(cursor, atoms)
    RequireArch((cursor.Offset, cursor.NextIndex), (start, counter), "CMgr part start")
    classes, objects = cursor.Classes.copy(), cursor.Objects.copy()
    ids = ReadCmgrPartEnd(cursor, Generation=19000, ConditionOne=False)
    RequireArch(set(ids), set(atoms), "CMgr part atoms match base links")
    RequireArch(cursor.Offset, end, "CMgr part return")
    part_indices = tuple(index for index, name in objects.items() if name == KConfigClass)
    RequireArch(part_indices, (4,), "CMgr original part allocation")
    ReadCmgrAliases(cursor, part_indices[0])
    RequireArch(
        (cursor.Offset, cursor.NextIndex, cursor.Classes, cursor.Objects),
        (end + 14, counter, classes, objects),
        "CMgr part and alias map",
    )
    next_tag = ReadTag(cursor.BlobValue, cursor.Offset)
    RequireArch(
        (next_tag.kind, next_tag.class_name, next_tag.schema, next_tag.wide),
        (KDefinitionKind, KExtObjectClass, 1, False),
        "CMgr external object after part aliases",
    )
    return ids, cursor.BlobValue[start:end], saved_links


# The independent link map must grow the same archive namespace as the saved nodes.
def verify_link_map(
    writer: ArchiveWriter,
    cursor: ArchiveCursor,
    ids: tuple[int, ...],
    tree_ids: tuple[int, ...],
    saved: bytes,
) -> str:
    WriteCmgrLinks(writer, 19000, tuple(zip(ids, tree_ids, strict=True)))
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr emitted link allocator",
    )
    RequireArch(writer.build() == saved, True, "CMgr linked atom reconstruction")
    return sha256(saved).hexdigest()


# exact bytes and writer allocator stability must hold for both saved map orders
def verify_part_end(
    cursor: ArchiveCursor, recipe: str, tree_ids: tuple[int, ...], asset: str
) -> tuple[str, str | None]:
    links_writer = ArchiveWriter()
    links_writer.SetNextIndex(cursor.NextIndex)
    links_writer.classes.update((name, index) for index, name in cursor.Classes.items())
    ids, saved, saved_links = read_part_evidence(cursor, recipe, tree_ids)
    links_digest = None
    if len(tree_ids) <= 1:
        links_digest = verify_link_map(links_writer, cursor, ids, tree_ids, saved_links)
    writer = ArchiveWriter()
    writer.SetNextIndex(cursor.NextIndex)
    writer.classes.update((name, index) for index, name in cursor.Classes.items())
    classes = writer.classes.copy()
    WriteCmgrPartEnd(writer, Generation=19000, ConditionOne=False, AtomIds=ids)
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, classes),
        "CMgr part write allocator",
    )
    RequireArch(writer.build() == saved, True, f"CMgr part reconstruction in {asset}")
    return sha256(saved).hexdigest(), links_digest
