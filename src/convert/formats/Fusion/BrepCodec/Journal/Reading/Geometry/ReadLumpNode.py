from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadLumpNode(Cursor: FieldCursor) -> LumpNode:
    Prefix = ReadPrefixMut(Cursor)
    NextLump = ReadRefMut(Cursor)
    FirstShell = ReadRefMut(Cursor)
    OwnerBody = ReadRefMut(Cursor)
    return LumpNode(Prefix, NextLump, FirstShell, OwnerBody)
