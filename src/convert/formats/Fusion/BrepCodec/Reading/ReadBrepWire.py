from convert.formats.Fusion.BrepCodec.Reading.BrepWire import BrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepHeader import ReadBrepHeadMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmRecord,
    AsmTable,
    ReadAsmName,
    ReadAsmRecord,
)


def ReadBrepWire(Payload: bytes, HasHistory: bool) -> BrepWire:
    if type(Payload) is not bytes or not 0 < len(Payload) <= 2 * 1024 * 1024:
        raise ValueError("Invalid or oversized Fusion BRep payload")
    Cursor = MetaCursor(Payload)
    Header, Stamp = ReadBrepHeadMut(Cursor, HasHistory)
    Count = 35 if HasHistory else 59
    Records = tuple(ReadAsmRecord(Cursor, ReadAsmName(Cursor)) for _ in range(Count))
    Journal: tuple[AsmRecord, ...] = ()
    if HasHistory:
        if ReadAsmName(Cursor) != "Begin-of-ASM-History-Data":
            raise ValueError("Missing Fusion BRep insertion journal")
        Journal = tuple(ReadAsmRecord(Cursor, ReadAsmName(Cursor)) for _ in range(3))
        if ReadAsmName(Cursor) != "End-of-ASM-History-Section":
            raise ValueError("Unsupported Fusion BRep archived revisions")
    if ReadAsmName(Cursor) != "End-of-ASM-data" or Cursor.Offset != len(Payload):
        raise ValueError("Trailing or unterminated Fusion BRep data")
    return BrepWire(Header, Stamp, AsmTable(Header.RootCount, Records), Journal)
