from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# feature bookkeeping clocks belong to a separate typed primary record
KFeatureClock = "6CCF41D5-40BE-48ED-A834-18F3EAED6C57"


# the actor must reciprocate the exact same clock in exactly one sequence entry
def ReadFaceClock(
    BulkData: bytes, Owners: dict[int, RecordSpan], ActorId: int
) -> tuple[int, int]:
    SpanValue = Owners.get(ActorId)
    if SpanValue is None or SpanValue.EndOffset - SpanValue.PayloadOffset < 13:
        raise ValueError("Missing Fusion feature clock footer")
    Footer = MetaCursor(BulkData[SpanValue.EndOffset - 13 : SpanValue.EndOffset])
    ClockId = ReadNativeRef(Footer)
    if Footer.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion feature clock footer")
    Cursor = SelectCursor(BulkData, Owners, ClockId, KFeatureClock)
    if Cursor.TakeBytes(6) != bytes(6) or any(
        FlagValue not in (0, 1) for FlagValue in Cursor.TakeBytes(2)
    ):
        raise ValueError("Unsupported Fusion feature clock prefix")
    Count = Cursor.ReadCount(100000)
    if len(Cursor.DataValue) != 39 + 19 * Count:
        raise ValueError("Invalid Fusion feature clock record extent")
    Values: list[int] = []
    for _ in range(Count):
        EntryId, Timestamp = ReadNativeRef(Cursor), Cursor.ReadLong()
        if EntryId not in Owners:
            raise ValueError("Fusion feature clock entry leaves the primary table")
        if EntryId == ActorId:
            Values.append(Timestamp)
    Backlink, ClockValue = ReadNativeRef(Cursor), Cursor.ReadLong()
    if (
        Backlink != ActorId
        or Values != [ClockValue]
        or not 0 < ClockValue < (1 << 53)
        or Cursor.TakeBytes(8) != bytes(8)
    ):
        raise ValueError("Fusion feature clock owner or sequence entry disagrees")
    return ClockId, ClockValue
