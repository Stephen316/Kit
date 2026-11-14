from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
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


def ReadFaceNode(Cursor: FieldCursor) -> FaceNode:
    Prefix = ReadPrefixMut(Cursor)
    NextFace = ReadRefMut(Cursor)
    FirstLoop = ReadRefMut(Cursor)
    OwnerShell = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    Surface = ReadRefMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    DoubleSided = IsLogicalMut(Cursor)
    Contained = IsLogicalMut(Cursor) if DoubleSided else None
    return FaceNode(
        Prefix,
        NextFace,
        FirstLoop,
        OwnerShell,
        Surface,
        Reversed,
        DoubleSided,
        Contained,
    )
