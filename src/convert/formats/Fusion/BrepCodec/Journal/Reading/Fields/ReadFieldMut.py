from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def ReadFieldMut(Cursor: FieldCursor) -> KAsmToken:
    if Cursor.Offset >= len(Cursor.Record.Tokens):
        raise ValueError("Truncated Fusion journal entity")
    Field = Cursor.Record.Tokens[Cursor.Offset]
    Cursor.Offset += 1
    return Field
