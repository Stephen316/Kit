from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import KPrismRecords
from convert.formats.Fusion.BrepCodec.Reading.BrepWire import BrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepHeader import ReadBrepHeadMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmTable,
    ReadAsmName,
    ReadAsmRecord,
)


def ReadPrismWire(Payload: bytes) -> BrepWire:
    if type(Payload) is not bytes or not 0 < len(Payload) <= 2 * 1024 * 1024:
        raise ValueError("Invalid or oversized prism history payload")
    Cursor = MetaCursor(Payload)
    Header, Stamp = ReadBrepHeadMut(Cursor, True)
    Records = tuple(
        ReadAsmRecord(Cursor, ReadAsmName(Cursor)) for _ in range(KPrismRecords)
    )
    if ReadAsmName(Cursor) != "Begin-of-ASM-History-Data":
        raise ValueError("Missing prism insertion journal")
    Journal = tuple(ReadAsmRecord(Cursor, ReadAsmName(Cursor)) for _ in range(3))
    if ReadAsmName(Cursor) != "End-of-ASM-History-Section":
        raise ValueError("Archived prism revisions are unsupported")
    if ReadAsmName(Cursor) != "End-of-ASM-data" or Cursor.Offset != len(Payload):
        raise ValueError("Trailing or unterminated prism history")
    return BrepWire(Header, Stamp, AsmTable(Header.RootCount, Records), Journal)
