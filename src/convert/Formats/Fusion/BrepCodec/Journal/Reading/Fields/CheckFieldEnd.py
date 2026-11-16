from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor


# invalid field end input must fail here so revision ownership survives native history reconstruction
def CheckFieldEnd(Cursor: FieldCursor) -> None:
    if Cursor.Offset != len(Cursor.Record.Tokens):
        raise ValueError("Uninterpreted Fusion journal entity fields")
