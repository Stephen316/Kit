from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.CheckFieldEnd import (
    CheckFieldEnd,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadStreamNode(Record: AsmRecord) -> StreamState:
    if Record.Name != "history_stream":
        raise ValueError("Missing Fusion history-stream record")
    Cursor = FieldCursor(Record)
    Numbers = tuple(ReadLongMut(Cursor) for _ in range(4))
    References = tuple(ReadRefMut(Cursor) for _ in range(4))
    CheckFieldEnd(Cursor)
    return StreamState(*Numbers, *References)
