from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadRuleMut import (
    ReadSubtypeMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


# the pcurve node operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadPcurveNode(Cursor: FieldCursor) -> PcurveNode:
    Prefix = ReadPrefixMut(Cursor)
    FormValue = ReadLongMut(Cursor)
    if FormValue == 0:
        Reversed = IsLogicalMut(Cursor)
        Curve = ReadSubtypeMut(Cursor, "pcurve")
        OffsetU = ReadDoubleMut(Cursor)
        return PcurveNode(Prefix, Reversed, Curve, OffsetU, ReadDoubleMut(Cursor))
    if FormValue not in (-2, -1, 1, 2):
        raise ValueError("Unsupported Fusion pcurve form")
    CurveRef = ReadRefMut(Cursor)
    OffsetU = ReadDoubleMut(Cursor)
    OffsetV = ReadDoubleMut(Cursor)
    return PcurveNode(Prefix, False, None, OffsetU, OffsetV, FormValue, CurveRef)
