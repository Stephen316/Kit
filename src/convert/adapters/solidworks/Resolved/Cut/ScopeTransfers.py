from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Container.Archive import KObjectRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeOwner


# each transfer must reach an allocated configuration atom before scope can bind it
def ReadScopeXfer(Cursor: ArchiveCursor) -> tuple[int, ...]:
    Present, Count = Cursor.ReadInts("<iH")
    RequireArch(
        Present == 1 and Count in (1, 2), True, "one or two configured scope transfers"
    )
    Transfers = tuple(
        Cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)[2]
        for _ in range(Count)
    )
    RequireArch(len(set(Transfers)), Count, "distinct scope transfer objects")
    return Transfers


# transfers and result atom ids are different namespaces and precede both body lists
def ReadScopeLead(
    Cursor: ArchiveCursor,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    RequireArch(Cursor.ReadInts("<i3H"), (0, 0, 0, 0), "guarded scope feature fields")
    CutTransfers, ParentTransfers = ReadScopeXfer(Cursor), ReadScopeXfer(Cursor)
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (2,), "two saved scope atom identities")
    AtomIds = Cursor.ReadInts("<2i")
    RequireArch(
        0 < AtomIds[0] < AtomIds[1], True, "distinct ordered scope atom identities"
    )
    RequireArch(Cursor.ReadInts("<i"), (3,), "witnessed scope atom body type")
    return CutTransfers, ParentTransfers, AtomIds


# the actual configured atom map supplies the cut transfers and permits the unselected boss to remain
def CheckScopeXfer(
    Cursor: ArchiveCursor,
    Owners: tuple[ScopeOwner, ScopeOwner],
    SelectedCount: int,
    CutTransfers: tuple[int, ...],
    ParentTransfers: tuple[int, ...],
) -> None:
    BossObjects = {Owner.TransferObject for Owner in Owners}
    AtomObjects = {
        Index for Index, ClassName in Cursor.Objects.items() if ClassName == "moAtom_c"
    }
    RequireArch(
        len(BossObjects) == 2 and BossObjects <= AtomObjects,
        True,
        "two earlier boss transfer allocations",
    )
    RequireArch(
        set(ParentTransfers),
        {Owner.TransferObject for Owner in Owners[:SelectedCount]},
        "scope parents agree with the witnessed body roster",
    )
    RequireArch(
        set(CutTransfers),
        AtomObjects - BossObjects,
        "scope cut transfers are the remaining configured atoms",
    )
    RequireArch(
        len(CutTransfers),
        len(ParentTransfers),
        "matching cut and parent transfer counts",
    )
