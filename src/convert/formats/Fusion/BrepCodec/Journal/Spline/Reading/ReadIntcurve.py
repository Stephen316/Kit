from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadRuleMut import (
    ReadSubtypeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
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


def ReadIntcurve(Cursor: FieldCursor) -> IntcurveNode:
    Prefix = ReadPrefixMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    Curve = ReadSubtypeMut(Cursor, "curve")
    Lower = ReadBoundMut(Cursor)
    Upper = ReadBoundMut(Cursor)
    return IntcurveNode(Prefix, Reversed, Curve, Lower, Upper)
