from convert.Formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


# the wire node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadWireNode(Cursor: FieldCursor) -> WireNode:
    Prefix = ReadPrefixMut(Cursor)
    NextWire = ReadRefMut(Cursor)
    FirstCoedge = ReadRefMut(Cursor)
    OwnerShell = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    return WireNode(Prefix, NextWire, FirstCoedge, OwnerShell, IsLogicalMut(Cursor))
