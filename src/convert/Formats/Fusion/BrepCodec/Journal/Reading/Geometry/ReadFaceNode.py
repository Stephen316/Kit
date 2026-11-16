from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
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


# the face node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
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
