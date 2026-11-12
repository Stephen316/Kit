from convert.formats.Fusion.HistoryGroup import KGroupGuid, HistoryGroup, ReadGroup
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan

# each declared history record owns an explicit sequence independent of offsets
KHistoryGuid = "2F4C1849-1A5A-4F6C-A086-8DD445CBF94B"


# bounded ordered references establish native history without inferring a timeline
def ReadHistory(
    BulkData: bytes, History: RecordSpan, Owners: dict[int, RecordSpan]
) -> tuple[int, tuple[int, ...], tuple[HistoryGroup, ...]]:
    BodyValue = BulkData[History.PayloadOffset + 4 : History.EndOffset]
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Invalid Fusion history prefix")
    OwnerId = ReadNativeRef(Cursor)
    Count = Cursor.ReadCount(100000)
    if len(BodyValue) != 17 + 11 * Count or OwnerId not in Owners:
        raise ValueError("Invalid Fusion history length or owner")
    Entries = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if len(set(Entries)) != Count or any(Entry not in Owners for Entry in Entries):
        raise ValueError("Duplicate or missing Fusion history entry")
    Groups: list[HistoryGroup] = []
    MemberIds: set[int] = set()
    for Index, Entry in enumerate(Entries):
        GroupSpan = Owners[Entry]
        if GroupSpan.ClassGuid != KGroupGuid:
            continue
        Group = ReadGroup(
            BulkData[GroupSpan.PayloadOffset + 4 : GroupSpan.EndOffset], Entry
        )
        Members = Group.MemberIds
        if (
            Entries[Index + 1 : Index + 1 + len(Members)] != Members
            or any(Owners[Member].ClassGuid == KGroupGuid for Member in Members)
            or MemberIds.intersection(Members)
        ):
            raise ValueError("Invalid Fusion history group membership")
        Groups.append(Group)
        MemberIds.update(Members)
    return OwnerId, Entries, tuple(Groups)
