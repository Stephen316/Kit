from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadShellNode(Cursor: FieldCursor) -> ShellNode:
    Prefix = ReadPrefixMut(Cursor)
    NextShell = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    FirstFace = ReadRefMut(Cursor)
    FirstWire = ReadRefMut(Cursor)
    OwnerLump = ReadRefMut(Cursor)
    return ShellNode(Prefix, NextShell, FirstFace, OwnerLump, FirstWire)
