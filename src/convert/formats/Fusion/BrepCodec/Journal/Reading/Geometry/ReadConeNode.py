from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
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


def ReadConeNode(Cursor: FieldCursor) -> ConeNode:
    Prefix = ReadPrefixMut(Cursor)
    OriginCm = ReadVectorMut(Cursor, 19)
    AxisVector = ReadVectorMut(Cursor, 20)
    MajorAxisCm = ReadVectorMut(Cursor, 20)
    EllipseRatio = ReadDoubleMut(Cursor)
    EllipseLower = ReadBoundMut(Cursor)
    EllipseUpper = ReadBoundMut(Cursor)
    SineAngle = ReadDoubleMut(Cursor)
    CosineAngle = ReadDoubleMut(Cursor)
    UScaleCm = ReadDoubleMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    ULower = ReadBoundMut(Cursor)
    UUpper = ReadBoundMut(Cursor)
    VLower = ReadBoundMut(Cursor)
    VUpper = ReadBoundMut(Cursor)
    return ConeNode(
        Prefix,
        OriginCm,
        AxisVector,
        MajorAxisCm,
        EllipseRatio,
        EllipseLower,
        EllipseUpper,
        SineAngle,
        CosineAngle,
        UScaleCm,
        Reversed,
        ULower,
        UUpper,
        VLower,
        VUpper,
    )
