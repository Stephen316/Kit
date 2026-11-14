from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadSubtrans import (
    ReadSubtrans,
)


def ReadTransScope(Cursor: FieldCursor) -> SubtransNode | SubtypeRef:
    Scope = ReadScopeMut(Cursor, "subtrans")
    if isinstance(Scope, SubtypeRef):
        return Scope
    if Scope != "t_spl_subtrans_object":
        raise ValueError("Unsupported Fusion T-spline subtransform subtype")
    return ReadSubtrans(Cursor)
