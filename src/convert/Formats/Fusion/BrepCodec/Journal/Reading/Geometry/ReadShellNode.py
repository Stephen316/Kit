from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


# the shell node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadShellNode(Cursor: FieldCursor) -> ShellNode:
    Prefix = ReadPrefixMut(Cursor)
    NextShell = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    FirstFace = ReadRefMut(Cursor)
    FirstWire = ReadRefMut(Cursor)
    OwnerLump = ReadRefMut(Cursor)
    return ShellNode(Prefix, NextShell, FirstFace, OwnerLump, FirstWire)
