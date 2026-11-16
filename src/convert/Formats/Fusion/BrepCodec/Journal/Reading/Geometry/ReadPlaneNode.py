from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


# the plane node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadPlaneNode(Cursor: FieldCursor) -> PlaneNode:
    Prefix = ReadPrefixMut(Cursor)
    OriginCm = ReadVectorMut(Cursor, 19)
    Normal = ReadVectorMut(Cursor, 20)
    ReferenceAxis = ReadVectorMut(Cursor, 20)
    ReversedV = IsLogicalMut(Cursor)
    ULower = ReadBoundMut(Cursor)
    UUpper = ReadBoundMut(Cursor)
    VLower = ReadBoundMut(Cursor)
    VUpper = ReadBoundMut(Cursor)
    return PlaneNode(
        Prefix,
        OriginCm,
        Normal,
        ReferenceAxis,
        ReversedV,
        ULower,
        UUpper,
        VLower,
        VUpper,
    )
