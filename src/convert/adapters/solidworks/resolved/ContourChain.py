from collections.abc import Sequence
from typing import TypedDict

from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor


# the contour chain has its own object identity and names the saved perimeter members
class ProfileChain(TypedDict):
    object_index: int
    edge_ids: tuple[int, ...]
    end: int


# the four saved members must remain attached to their typed chain allocation
def ReadChain(Cursor: ArchiveCursor, KindValue: str = KClassRefKind) -> ProfileChain:
    _, _, Index = Cursor.TakePointer(("moSketchChain_c",), KindValue, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (4,), "four profile chain edges")
    EdgeIds = Cursor.ReadInts("<4I")
    RequireArch(Cursor.ReadInts("<H"), (1,), "one secondary chain id")
    _ = Cursor.ReadInts("<I6i")
    RequireArch(Cursor.ReadText(), "", "empty chain label")
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent chain handles")
    _, Pairs = Cursor.ReadInts("<2I")
    RequireArch(Pairs, 0, "empty chain pair map")
    Cursor.ReadNull()
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "guarded modern chain trailer")
    return {"object_index": Index, "edge_ids": EdgeIds, "end": Cursor.Offset}


# a body bearing rectangle needs a chain over exactly its own sketch perimeter
def ReadChainState(
    Cursor: ArchiveCursor, HasAtom: bool, EdgeIds: Sequence[int]
) -> ProfileChain | None:
    Count = int(HasAtom)
    RequireArch(
        Cursor.ReadInts("<Ii"), (Count, Count), "witnessed rectangle chain state"
    )
    if not HasAtom:
        return None
    Chain = ReadChain(Cursor, KDefinitionKind)
    RequireArch(
        sorted(Chain["edge_ids"]),
        sorted(EdgeIds),
        "body chain covers the sketch perimeter",
    )
    return Chain
