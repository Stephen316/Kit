from convert.formats.Fusion.BrepCodec.Reading.BrepWire import BrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepHeader import ReadBrepHeadMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmTable,
    ReadAsmName,
    ReadAsmRecord,
)


def ReadSnapWire(Payload: bytes) -> BrepWire:
    if type(Payload) is not bytes or not 0 < len(Payload) <= 2 * 1024 * 1024:
        raise ValueError("Invalid or oversized cuboid snapshot")
    Cursor = MetaCursor(Payload)
    Header, Stamp = ReadBrepHeadMut(Cursor, False)
    Records = tuple(ReadAsmRecord(Cursor, ReadAsmName(Cursor)) for _ in range(168))
    if ReadAsmName(Cursor) != "End-of-ASM-data" or Cursor.Offset != len(Payload):
        raise ValueError("Unterminated or trailing cuboid snapshot data")
    return BrepWire(Header, Stamp, AsmTable(4, Records), ())
