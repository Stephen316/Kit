from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


def ReadEllipseNode(Cursor: FieldCursor) -> EllipseNode:
    Prefix = ReadPrefixMut(Cursor)
    OriginCm = ReadVectorMut(Cursor, 19)
    Normal = ReadVectorMut(Cursor, 20)
    MajorAxisCm = ReadVectorMut(Cursor, 20)
    EllipseRatio = ReadDoubleMut(Cursor)
    LowerBound = ReadBoundMut(Cursor)
    UpperBound = ReadBoundMut(Cursor)
    return EllipseNode(
        Prefix, OriginCm, Normal, MajorAxisCm, EllipseRatio, LowerBound, UpperBound
    )
