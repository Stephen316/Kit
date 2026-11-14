from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor


def CheckFieldEnd(Cursor: FieldCursor) -> None:
    if Cursor.Offset != len(Cursor.Record.Tokens):
        raise ValueError("Uninterpreted Fusion journal entity fields")
