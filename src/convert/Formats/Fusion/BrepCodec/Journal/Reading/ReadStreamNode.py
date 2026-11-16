from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.CheckFieldEnd import (
    CheckFieldEnd,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# history streams need stable state links so journal reconstruction can preserve native revision ownership
def ReadStreamNode(Record: AsmRecord) -> StreamState:
    if Record.Name != "history_stream":
        raise ValueError("Missing Fusion history-stream record")
    Cursor = FieldCursor(Record)
    Numbers = tuple(ReadLongMut(Cursor) for _ in range(4))
    References = tuple(ReadRefMut(Cursor) for _ in range(4))
    CheckFieldEnd(Cursor)
    return StreamState(*Numbers, *References)
