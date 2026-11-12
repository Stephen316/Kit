from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# the history backend distinguishes saved design membership from the alternate body context
KBodyHistory = "74CA4562-59F8-4C97-8AD1-F8297C21F9AA"

# the history context proves the collection is scoped to the selected component
KHistoryScope = "372234A0-2A6C-4122-8047-E74DBA04F326"

# optional auxiliary metadata has its own collection backlink
KBodyAuxiliary = "E55D0457-898F-4A8E-B1A5-C85BDBA8794F"


# skip the opaque mapping pairs while checking the separate collection role backlink
def ReadBodyBackend(
    BulkData: bytes, Owners: dict[int, RecordSpan], Identity: int, CollectionId: int
) -> None:
    Mapping = SelectCursor(BulkData, Owners, Identity, KBodyHistory)
    if Mapping.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body history backend prefix")
    Count = Mapping.ReadCount(100000)
    Mapping.Offset += 16 * Count
    if ReadNativeRef(Mapping) != CollectionId or Mapping.TakeBytes(1) != bytes(1):
        raise ValueError("Fusion body history backend owner disagrees")
    PathValue = Mapping.ReadText(True)
    if Mapping.Offset != len(Mapping.DataValue) or (
        (Count == 0 and PathValue)
        or (
            Count > 0
            and (
                not PathValue.startswith("BREP.")
                or not PathValue.endswith(".smbh")
                or "/" in PathValue
                or "\\" in PathValue
            )
        )
    ):
        raise ValueError("Unsupported Fusion body history backend suffix")


# optional auxiliary ownership avoids accepting unrelated typed records
def ReadBodyAux(
    BulkData: bytes, Owners: dict[int, RecordSpan], Identity: int, CollectionId: int
) -> None:
    Auxiliary = SelectCursor(BulkData, Owners, Identity, KBodyAuxiliary)
    if Auxiliary.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion body collection auxiliary prefix")
    _ = Auxiliary.TakeBytes(8)
    if ReadNativeRef(Auxiliary) != CollectionId or Auxiliary.TakeBytes(1) != bytes(1):
        raise ValueError("Fusion body collection auxiliary owner disagrees")
    Count = Auxiliary.ReadCount(100000)
    if Auxiliary.Offset + Count * 8 != len(Auxiliary.DataValue):
        raise ValueError("Unsupported Fusion body collection auxiliary count")


# two independently owned contexts distinguish the saved design body collection role
def ReadCurrentRole(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Cursor: MetaCursor,
    CollectionId: int,
    ComponentId: int,
) -> int:
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Unsupported Fusion body collection role prefix")
    AuxiliaryId = ReadOptRefMut(Cursor)
    if AuxiliaryId is not None:
        ReadBodyAux(BulkData, Owners, AuxiliaryId, CollectionId)
    BackendId = ReadNativeRef(Cursor)
    ReadBodyBackend(BulkData, Owners, BackendId, CollectionId)
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Unsupported Fusion body collection context prefix")
    Context = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KHistoryScope)
    if (
        len(Context.DataValue) != 23
        or Context.TakeBytes(12) != bytes(12)
        or ReadNativeRef(Context) != ComponentId
        or Cursor.TakeBytes(1) != bytes(1)
    ):
        raise ValueError("Fusion body collection context disagrees")
    return BackendId
