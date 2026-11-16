from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the field operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadFieldMut(Cursor: FieldCursor) -> KAsmToken:
    if Cursor.Offset >= len(Cursor.Record.Tokens):
        raise ValueError("Truncated Fusion journal entity")
    Field = Cursor.Record.Tokens[Cursor.Offset]
    Cursor.Offset += 1
    return Field
