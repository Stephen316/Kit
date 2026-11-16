from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSysAttrib import (
    ReadSysLinks,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


# the name body operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadNameBody(Cursor: FieldCursor, HasNumber: bool) -> NameAttrib:
    Links = ReadSysLinks(Cursor)
    Actions = (
        ReadLongMut(Cursor, 21),
        ReadLongMut(Cursor, 21),
        ReadLongMut(Cursor, 21),
        ReadLongMut(Cursor, 21),
    )
    NameText = ReadTextMut(Cursor)
    NumberValue = ReadLongMut(Cursor, 23) if HasNumber else None
    return NameAttrib(Links, Actions, NameText, NumberValue)


# the name node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadNameNode(Cursor: FieldCursor) -> NameAttrib:
    return ReadNameBody(Cursor, False)


# the long name operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadLongName(Cursor: FieldCursor) -> NameAttrib:
    return ReadNameBody(Cursor, True)
