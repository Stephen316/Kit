from convert.formats.Fusion.Assembly.Solids.CreatorScopes import (
    CreatorScope,
    KScopeOwner,
    KScopeSnapshot,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor


# creation bookkeeping names the parent scope used when the occurrence was placed
def ReadSnapParent(
    BulkData: bytes, Owners: dict[int, RecordSpan], Scope: CreatorScope
) -> int:
    if Scope.SnapshotId is None:
        raise ValueError("Fusion authoring scope has no creation snapshot")
    Snapshot = SelectCursor(BulkData, Owners, Scope.SnapshotId, KScopeSnapshot)
    Snapshot.Offset = len(Snapshot.DataValue) - 23
    Workbook = SelectCursor(BulkData, Owners, ReadNativeRef(Snapshot), KScopeOwner)
    if len(Workbook.DataValue) != 96 or Workbook.TakeBytes(12) != bytes.fromhex(
        "000000000000010103000000"
    ):
        raise ValueError("Unsupported Fusion creation scope bookkeeping")
    Parent = ReadNativeRef(Workbook)
    _ = Workbook.TakeBytes(8)
    if ReadNativeRef(Workbook) != Scope.ScopeId:
        raise ValueError("Fusion creation snapshot own scope disagrees")
    _ = Workbook.TakeBytes(8)
    if ReadNativeRef(Workbook) != Scope.SnapshotId:
        raise ValueError("Fusion creation scope snapshot reference disagrees")
    Stamp = Workbook.TakeBytes(8)
    if ReadNativeRef(Workbook) != Scope.SnapshotId or Workbook.TakeBytes(8) != Stamp:
        raise ValueError("Fusion creation scope repeated snapshot disagrees")
    if Workbook.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion creation scope bookkeeping suffix")
    return Parent
