from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadRuleMut import (
    ReadSubtypeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)


def ReadSplineNode(Cursor: FieldCursor) -> SplineNode:
    Prefix = ReadPrefixMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    Surface = ReadSubtypeMut(Cursor, "surface")
    ULower = ReadBoundMut(Cursor)
    UUpper = ReadBoundMut(Cursor)
    VLower = ReadBoundMut(Cursor)
    VUpper = ReadBoundMut(Cursor)
    return SplineNode(Prefix, Reversed, Surface, ULower, UUpper, VLower, VUpper)
