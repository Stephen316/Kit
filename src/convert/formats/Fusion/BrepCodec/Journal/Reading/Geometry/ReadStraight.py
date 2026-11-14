from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)


def ReadStraight(Cursor: FieldCursor) -> StraightNode:
    return StraightNode(
        ReadPrefixMut(Cursor),
        ReadVectorMut(Cursor, 19),
        ReadVectorMut(Cursor, 20),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
    )
