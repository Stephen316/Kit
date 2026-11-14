from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadLoopNode(Cursor: FieldCursor) -> LoopNode:
    Prefix = ReadPrefixMut(Cursor)
    NextLoop = ReadRefMut(Cursor)
    FirstCoedge = ReadRefMut(Cursor)
    OwnerFace = ReadRefMut(Cursor)
    return LoopNode(Prefix, NextLoop, FirstCoedge, OwnerFace)
