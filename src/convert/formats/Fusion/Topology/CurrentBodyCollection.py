from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid
from convert.formats.Fusion.Topology.BodyCollection import (
    KBodyCollection,
    ReadBodyOwner,
)
from convert.formats.Fusion.Topology.BodyCollectionRole import ReadCurrentRole

# mixed collections store mesh references separately from the repeated native body subset
KMeshGuid = "EA90DA22-556C-4C61-89BB-20C2681B7A9D"


# the saved body list keeps its exact history backend even when mesh members are present
def ReadCurrentBody(
    BulkData: bytes, Owners: dict[int, RecordSpan], CollectionId: int, ComponentId: int
) -> tuple[tuple[int, ...], int]:
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KBodyCollection)
    Prefix = Cursor.TakeBytes(2)
    if Prefix == b"\0\1" and Cursor.ReadWord() != 0:
        raise ValueError("Unsupported Fusion body collection attributes")
    if Prefix not in (b"\0\0", b"\0\1") or Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion body collection prefix")
    _ = Cursor.TakeBytes(4)
    Count = Cursor.ReadCount(100000)
    if Cursor.Offset + 11 * Count > len(Cursor.DataValue):
        raise ValueError("Truncated Fusion body collection membership")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if len(set(Members)) != Count:
        raise ValueError("Fusion body collection repeats member identity")
    BodyIds: list[int] = []
    for Identity in Members:
        SpanValue = Owners.get(Identity)
        if SpanValue is None or SpanValue.ClassGuid not in (KBodyGuid, KMeshGuid):
            raise ValueError("Fusion body collection has an unsupported member")
        if SpanValue.ClassGuid == KBodyGuid:
            BodyIds.append(Identity)
    BackendId = ReadCurrentRole(BulkData, Owners, Cursor, CollectionId, ComponentId)
    BodyCount = Cursor.ReadCount(100000)
    if (
        BodyCount != len(BodyIds)
        or Cursor.Offset + 11 * (BodyCount + 1) != len(Cursor.DataValue)
        or [ReadNativeRef(Cursor) for _ in range(BodyCount)] != BodyIds
    ):
        raise ValueError("Fusion body collection repeated membership disagrees")
    if ReadNativeRef(Cursor) != ComponentId or any(
        ReadBodyOwner(BulkData, Owners, Identity) != CollectionId
        for Identity in BodyIds
    ):
        raise ValueError("Fusion body collection ownership disagrees")
    return tuple(BodyIds), BackendId


# inventory callers use ordered bodies without loading geometry from the history backend
def ReadCurrentList(
    BulkData: bytes, Owners: dict[int, RecordSpan], CollectionId: int, ComponentId: int
) -> tuple[int, ...]:
    BodyIds, _ = ReadCurrentBody(BulkData, Owners, CollectionId, ComponentId)
    return BodyIds
