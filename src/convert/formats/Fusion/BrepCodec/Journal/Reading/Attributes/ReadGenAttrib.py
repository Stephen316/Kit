from convert.formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSysAttrib import (
    ReadSysLinks,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


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


def ReadNameNode(Cursor: FieldCursor) -> NameAttrib:
    return ReadNameBody(Cursor, False)


def ReadLongName(Cursor: FieldCursor) -> NameAttrib:
    return ReadNameBody(Cursor, True)
