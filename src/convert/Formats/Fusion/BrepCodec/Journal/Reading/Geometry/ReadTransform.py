from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)


# the transform operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadTransform(Cursor: FieldCursor) -> TransformNode:
    Attribute = ReadRefMut(Cursor)
    EntityTag = ReadLongMut(Cursor)
    ColumnX = ReadVectorMut(Cursor, 20)
    ColumnY = ReadVectorMut(Cursor, 20)
    ColumnZ = ReadVectorMut(Cursor, 20)
    TranslationCm = ReadVectorMut(Cursor, 20)
    ScaleFactor = ReadDoubleMut(Cursor)
    Rotation = IsLogicalMut(Cursor)
    Reflection = IsLogicalMut(Cursor)
    Sheared = IsLogicalMut(Cursor)
    return TransformNode(
        Attribute,
        EntityTag,
        ColumnX,
        ColumnY,
        ColumnZ,
        TranslationCm,
        ScaleFactor,
        Rotation,
        Reflection,
        Sheared,
    )
