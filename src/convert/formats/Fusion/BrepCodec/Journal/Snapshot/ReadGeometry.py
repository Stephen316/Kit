from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import (
    ReadEntitiesMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadGeometry(Payload: bytes) -> GeometryState:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KJournalBytes:
        raise ValueError("Invalid or oversized Fusion geometry payload")
    Cursor = MetaCursor(Payload)
    Header, Stamp = ReadModelHead(Cursor, False)
    Entities = ReadEntitiesMut(Cursor, "End-of-ASM-data", Header.IntWidth)
    if Cursor.Offset != len(Payload):
        raise ValueError("Trailing Fusion geometry bytes")
    Model = GeometryState(Header, Stamp, Entities)
    CheckGeometry(Model)
    return Model
