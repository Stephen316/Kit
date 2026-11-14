from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadRuleMut import (
    ReadRuleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.RuleWords import (
    KCurveCall,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadCoedgeNode import (
    ReadCoedgeNode,
)


def ReadTcoedgeNode(Cursor: FieldCursor) -> TcoedgeNode:
    BaseNode = ReadCoedgeNode(Cursor)
    RangeLower = ReadDoubleMut(Cursor)
    RangeUpper = ReadDoubleMut(Cursor)
    CurveRef = ReadRefMut(Cursor)
    CurveForm = ReadLongMut(Cursor)
    Curve = ReadRuleMut(Cursor, KCurveCall)
    Stamp = ReadLongMut(Cursor)
    return TcoedgeNode(
        BaseNode, RangeLower, RangeUpper, CurveRef, CurveForm, Curve, Stamp
    )
