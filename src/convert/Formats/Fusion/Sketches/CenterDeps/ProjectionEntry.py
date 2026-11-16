from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.Projections.ProjController import KProjEntry

# zero progenitor attributes distinguish this origin point from projected edges
KOriginOutName = "CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C"


# the original cache output must reciprocate a distinct typed naming record
def ReadProjEntry(
    BulkData: bytes, Owners: dict[int, RecordSpan], EntryId: int
) -> tuple[int, int, int]:
    Entry = SelectCursor(BulkData, Owners, EntryId, KProjEntry)
    if len(Entry.DataValue) != 33 or Entry.TakeBytes(6) != b"\0\0\1" + bytes(3):
        raise ValueError("Unsupported Fusion point projection output entry")
    NameId = ReadNativeRef(Entry)
    OutputId = Entry.ReadLong()
    if Entry.ReadLong() != 1:
        raise ValueError("Unsupported Fusion point projection output form")
    Naming = SelectCursor(BulkData, Owners, NameId, KOriginOutName)
    if len(Naming.DataValue) != 18 or Naming.TakeBytes(6) != b"\0\1" + bytes(4):
        raise ValueError("Unsupported Fusion origin projection naming layout")
    LeafId = ReadNativeRef(Naming)
    if Naming.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion origin projection naming trailer")
    return OutputId, NameId, LeafId
