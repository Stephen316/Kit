from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)


# the straight operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadStraight(Cursor: FieldCursor) -> StraightNode:
    return StraightNode(
        ReadPrefixMut(Cursor),
        ReadVectorMut(Cursor, 19),
        ReadVectorMut(Cursor, 20),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
    )
