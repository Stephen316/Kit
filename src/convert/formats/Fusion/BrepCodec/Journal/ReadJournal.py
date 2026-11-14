from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import (
    ReadEntitiesMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStatesMut import ReadStatesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStreamNode import (
    ReadStreamNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckJournal import (
    CheckJournal,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.WalkStates import WalkStates
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


def ReadJournal(Payload: bytes) -> JournalModel:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KJournalBytes:
        raise ValueError("Invalid or oversized Fusion journal payload")
    Cursor = MetaCursor(Payload)
    Header, Stamp = ReadModelHead(Cursor, True)
    Width = Header.IntWidth
    Active = ReadEntitiesMut(Cursor, "Begin-of-ASM-History-Data", Width)
    Stream = ReadStreamNode(ReadAsmRecord(Cursor, ReadAsmName(Cursor), Width))
    States = ReadStatesMut(Cursor, Width)
    Archived = ReadEntitiesMut(Cursor, "End-of-ASM-data", Width)
    if Cursor.Offset != len(Payload):
        raise ValueError("Trailing Fusion journal bytes")
    Model = JournalModel(Header, Stamp, len(Active), Active + Archived, Stream, States)
    CheckJournal(Model)
    _ = WalkStates(Model)
    return Model
