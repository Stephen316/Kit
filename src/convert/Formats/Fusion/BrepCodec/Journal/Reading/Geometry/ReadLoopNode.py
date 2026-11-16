from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


# the loop node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadLoopNode(Cursor: FieldCursor) -> LoopNode:
    Prefix = ReadPrefixMut(Cursor)
    NextLoop = ReadRefMut(Cursor)
    FirstCoedge = ReadRefMut(Cursor)
    OwnerFace = ReadRefMut(Cursor)
    return LoopNode(Prefix, NextLoop, FirstCoedge, OwnerFace)
