from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.EntityReaders import (
    KEntityReaders,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.CheckFieldEnd import (
    CheckFieldEnd,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadEntityNode(Record: AsmRecord) -> KJournalEntity:
    Reader = KEntityReaders.get(Record.Name)
    if Reader is None:
        raise ValueError("Unsupported Fusion journal entity kind: " + Record.Name)
    Cursor = FieldCursor(Record)
    Value = Reader(Cursor)
    CheckFieldEnd(Cursor)
    return Value
