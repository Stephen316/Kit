from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundNode import CheckRoundNode
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode


def ReadSphereNode(Cursor: FieldCursor) -> SphereNode:
    Value = SphereNode(
        ReadPrefixMut(Cursor),
        ReadVectorMut(Cursor, 19),
        ReadDoubleMut(Cursor),
        ReadVectorMut(Cursor, 20),
        ReadVectorMut(Cursor, 20),
        IsLogicalMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
    )
    CheckRoundNode(Value)
    return Value
