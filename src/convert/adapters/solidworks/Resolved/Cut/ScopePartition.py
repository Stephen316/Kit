from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import (
    ScopeBody,
    ScopePartition,
)


# partition pairs are corroborating saved identities with their own count and raw state
def ReadPartition(
    Cursor: ArchiveCursor, Bodies: tuple[ScopeBody, ...]
) -> ScopePartition:
    Offset = Cursor.Offset
    RequireArch(Cursor.ReadInts("<i"), (1,), "present scope partition marker")
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (State,) = Cursor.ReadInts("<i")
    RequireArch(Cursor.ReadInts("<4i"), (0,) * 4, "empty scope partition fields")
    (Count,) = Cursor.ReadInts("<i")
    Expected = (
        tuple(
            (BodyValue["recent_atom_id"], BodyValue["body_id"]) for BodyValue in Bodies
        )
        if len(Bodies) == 2
        else ()
    )
    RequireArch(Count, len(Expected), "witnessed scope partition pair count")
    Pairs = tuple(Cursor.ReadInts("<2i") for _ in range(Count))
    RequireArch(
        Pairs, Expected, "scope partition pairs agree with reached body inventory"
    )
    RequireArch(Cursor.ReadInts("<8i"), (0,) * 8, "empty scope partition return")
    return {
        "offset": Offset,
        "end": Cursor.Offset,
        "object_index": ObjectIndex,
        "raw_state": State,
        "atom_body_pairs": Pairs,
    }
