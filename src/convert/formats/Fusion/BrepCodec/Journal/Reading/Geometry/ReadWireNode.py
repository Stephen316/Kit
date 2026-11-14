from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadWireNode(Cursor: FieldCursor) -> WireNode:
    Prefix = ReadPrefixMut(Cursor)
    NextWire = ReadRefMut(Cursor)
    FirstCoedge = ReadRefMut(Cursor)
    OwnerShell = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    return WireNode(Prefix, NextWire, FirstCoedge, OwnerShell, IsLogicalMut(Cursor))
